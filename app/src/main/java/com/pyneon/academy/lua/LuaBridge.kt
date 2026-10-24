package com.pyneon.academy.lua

import android.content.Context
import com.pyneon.academy.lang.LanguageIds
import com.pyneon.academy.lang.LanguageRuntime
import com.pyneon.academy.lang.RunResult
import com.pyneon.academy.lang.VarInfo
import org.luaj.vm2.Globals
import org.luaj.vm2.LuaError
import org.luaj.vm2.LuaTable
import org.luaj.vm2.LuaValue
import org.luaj.vm2.Varargs
import org.luaj.vm2.compiler.LuaC
import org.luaj.vm2.lib.CoroutineLib
import org.luaj.vm2.lib.DebugLib
import org.luaj.vm2.lib.PackageLib
import org.luaj.vm2.lib.StringLib
import org.luaj.vm2.lib.TableLib
import org.luaj.vm2.lib.VarArgFunction
import org.luaj.vm2.lib.jse.JseBaseLib
import org.luaj.vm2.lib.jse.JseMathLib

/**
 * Lua 运行时（LuaJ 3.0.1，Lua 5.2 语义）。
 *
 * 与 [com.pyneon.academy.js.JsBridge] 相同的设计约束：
 * - 纯 JVM 实现，无 NDK、无 ABI 分包，APK 增量约 350 KB；
 * - 沙箱只装 Base / Table / String / Math / Coroutine 五个标准库，
 *   不装 io / os / luajava / debug / require 的资源查找器，
 *   脚本无法读写文件、执行命令或访问 Java 类；
 * - 看门狗用 [DebugLib.onInstruction] 指令钩子，等价于 JS 侧的
 *   instructionObserverThreshold 与 Python 侧的 settrace 看门狗；
 * - 所有求值串行化在一把锁上（LuaJ Globals 非线程安全）。
 */
object LuaBridge : LanguageRuntime {

    override val id: String = LanguageIds.LUA
    override val displayName: String = "Lua"
    override val fileExtension: String = "lua"
    override val grammarScope: String = "source.lua"
    override val version: String = "Lua 5.2 (LuaJ 3.0.1)"

    private const val DEFAULT_TIMEOUT = 8.0
    private const val TEST_TIMEOUT = 2.0
    private const val MAX_VARS = 40
    private const val MAX_REPR = 200
    private const val MAX_OUTPUT = 1_048_576

    override fun isAvailable(): Boolean = true

    override fun ensureStarted(context: Context) = Unit

    private val lock = Any()

    private class LuaTimeout : RuntimeException("lua-sandbox-timeout")

    private class OutputSink {
        val main: StringBuilder = StringBuilder()
        val err: StringBuilder = StringBuilder()
        var test: StringBuilder? = null
    }

    /**
     * 指令钩子看门狗：每次读 LuaBridge.deadlineNanos 的当前值，而不是构造时
     * 快照，否则同一 Globals 复用到第二次调用时会拿着旧的截止时间。
     */
    private class Watch : DebugLib() {
        override fun onInstruction(pc: Int, v: Varargs?, top: Int) {
            if (System.nanoTime() > deadlineNanos) throw LuaTimeout()
        }
    }

    private class Err(val type: String, val message: String, val traceback: String)

    override fun runCode(
        code: String,
        stdinLines: List<String>,
        timeoutSec: Double
    ): RunResult = synchronized(lock) { runOnce(code, timeoutSec) }

    override fun checkExercise(
        code: String,
        tests: List<String>,
        stdinLines: List<String>
    ): RunResult = synchronized(lock) { checkInternal(code, tests) }

    override fun warmup(): Boolean = try {
        runCode("return 1 + 1", emptyList(), 6.0).ok
    } catch (_: Throwable) {
        false
    }

    // ===== REPL：跨行累积，语法不完整时等待续行 =====

    private var replGlobals: Globals? = null
    private var replSink: OutputSink? = null
    private val replBuffer = StringBuilder()

    override fun replStart() {
        synchronized(lock) {
            replGlobals = null
            replSink = null
            replBuffer.setLength(0)
        }
    }

    override fun replPush(line: String): Pair<Boolean, String> = synchronized(lock) {
        val globals = replGlobals ?: newGlobals(OutputSink()).also { replGlobals = it }
        val sink = replSink ?: OutputSink().also {
            replSink = it
            installHost(globals, it)
        }
        val mark = sink.main.length
        if (line.isNotBlank()) replBuffer.append(line).append('\n')
        val source = replBuffer.toString().trim()
        if (source.isEmpty()) return@synchronized false to ""

        deadlineNanos = System.nanoTime() + (DEFAULT_TIMEOUT * 1e9).toLong()
        try {
            // 表达式回显：`1+2` 在 Lua 里不是合法语句。先按语句执行；若报的不是
            // 「不完整」类错误，再按 `return <表达式>` 重试，与 Python REPL 的
            // 表达式 repr 回显对齐。
            val result = try {
                globals.load(source, "<repl>").call()
            } catch (first: LuaError) {
                if (isIncomplete(first.message)) throw first
                globals.load("return " + source, "<repl>").call()
            }
            if (!result.isnil()) sink.main.append(result.tojstring()).append('\n')
            replBuffer.setLength(0)
            false to sink.main.substring(mark)
        } catch (t: LuaError) {
            if (isIncomplete(t.message)) {
                true to ""
            } else {
                replBuffer.setLength(0)
                sink.main.append(formatError(t, DEFAULT_TIMEOUT))
                false to sink.main.substring(mark)
            }
        } catch (t: Throwable) {
            replBuffer.setLength(0)
            sink.main.append(formatError(t, DEFAULT_TIMEOUT))
            false to sink.main.substring(mark)
        } finally {
            deadlineNanos = Long.MAX_VALUE
        }
    }

    // ===== 内部实现 =====

    @Volatile
    private var deadlineNanos: Long = Long.MAX_VALUE

    private fun newGlobals(sink: OutputSink): Globals {
        val globals = Globals()
        globals.load(JseBaseLib())
        globals.load(PackageLib())
        globals.load(TableLib())
        globals.load(StringLib())
        globals.load(JseMathLib())
        globals.load(CoroutineLib())
        globals.load(Watch())
        LuaC.install(globals)
        // PackageLib 默认用 ResourceFinder 读 classpath；置空后 require/loadfile 无法加载外部文件。
        globals.finder = org.luaj.vm2.lib.ResourceFinder { null }
        globals.set("debug", LuaValue.NIL)
        globals.set("dofile", LuaValue.NIL)
        globals.set("loadfile", LuaValue.NIL)
        installHost(globals, sink)
        return globals
    }

    private fun installHost(globals: Globals, sink: OutputSink) {
        globals.set("print", object : VarArgFunction() {
            override fun invoke(args: Varargs): Varargs {
                val target = sink.test ?: sink.main
                val sb = StringBuilder()
                for (i in 1..args.narg()) {
                    if (i > 1) sb.append('\t')
                    sb.append(args.arg(i).tojstring())
                }
                target.append(sb).append('\n')
                return LuaValue.NONE
            }
        })
        globals.set("input", object : VarArgFunction() {
            override fun invoke(args: Varargs): Varargs =
                throw LuaError("InputError: 运行台不支持交互式输入，请把数据直接写在代码里")
        })
    }

    private fun runOnce(code: String, timeoutSec: Double): RunResult {
        val startedAt = System.nanoTime()
        val sink = OutputSink()
        var error: Err? = null
        var variables: List<VarInfo> = emptyList()
        val globals = newGlobals(sink)
        val before = globals.keys().map { it.tojstring() }.toSet()
        deadlineNanos = System.nanoTime() + (timeoutSec * 1e9).toLong()
        try {
            globals.load(code, "<lesson>").call()
        } catch (t: Throwable) {
            error = mapError(t, timeoutSec)
        } finally {
            deadlineNanos = Long.MAX_VALUE
        }
        if (error == null) variables = snapshot(globals, before)
        return RunResult(
            ok = error == null,
            stdout = truncate(sink.main.toString()),
            stderr = truncate(sink.err.toString()),
            errorType = error?.type,
            errorMessage = error?.message,
            traceback = error?.traceback,
            durationMs = (System.nanoTime() - startedAt) / 1_000_000,
            variables = variables,
            passed = null
        )
    }

    private fun checkInternal(code: String, tests: List<String>): RunResult {
        val startedAt = System.nanoTime()
        val sink = OutputSink()
        val globals = newGlobals(sink)
        val before = globals.keys().map { it.tojstring() }.toSet()

        deadlineNanos = System.nanoTime() + (DEFAULT_TIMEOUT * 1e9).toLong()
        try {
            globals.load(code, "<lesson>").call()
        } catch (t: Throwable) {
            val e = mapError(t, DEFAULT_TIMEOUT)
            return RunResult(
                ok = false, passed = false,
                stdout = truncate(sink.main.toString()),
                stderr = truncate(sink.err.toString()),
                errorType = e.type, errorMessage = e.message, traceback = e.traceback,
                durationMs = (System.nanoTime() - startedAt) / 1_000_000,
                variables = emptyList()
            )
        } finally {
            deadlineNanos = Long.MAX_VALUE
        }

        val variables = snapshot(globals, before)
        val failures = mutableListOf<String>()
        tests.forEachIndexed { index, test ->
            sink.test = StringBuilder()
            deadlineNanos = System.nanoTime() + (TEST_TIMEOUT * 1e9).toLong()
            try {
                globals.load(test, "<lua-test-${index + 1}>").call()
            } catch (t: Throwable) {
                failures.add(firstLine(t.message ?: "断言未通过"))
            } finally {
                deadlineNanos = Long.MAX_VALUE
                sink.test = null
            }
        }
        val passed = failures.isEmpty()
        val message = if (passed) "" else
            "共 ${tests.size} 个用例，${failures.size} 个未通过；首个失败：${failures[0]}"
        return RunResult(
            ok = true, passed = passed,
            stdout = truncate(sink.main.toString()),
            stderr = truncate(sink.err.toString()),
            errorType = if (passed) null else "TestFailed",
            errorMessage = if (passed) null else message,
            traceback = null,
            durationMs = (System.nanoTime() - startedAt) / 1_000_000,
            variables = variables
        )
    }

    private fun isIncomplete(message: String?): Boolean {
        val m = message ?: return false
        return m.contains("'end' expected") ||
            m.contains("'until' expected") ||
            m.contains("unexpected symbol near '<eof>'") ||
            m.contains("'=' expected")
    }

    private fun mapError(t: Throwable, timeoutSec: Double): Err {
        val msg = t.message ?: ""
        val first = firstLine(msg)
        return when {
            t is LuaTimeout || msg.contains("lua-sandbox-timeout") ->
                Err("Timeout", "代码运行超过 %.1f 秒，已被强制中断（可能是死循环）".format(timeoutSec), "")
            msg.contains("'end' expected") || msg.contains("unexpected symbol") ||
                msg.contains("'=' expected") || msg.contains("'until' expected") ->
                Err("SyntaxError", first, msg)
            msg.contains("mismatch") || msg.contains("assert") ->
                Err("AssertionError", first, msg)
            else -> Err("RuntimeError", first, msg)
        }
    }

    private fun formatError(t: Throwable, timeoutSec: Double): String {
        val e = mapError(t, timeoutSec)
        return if (e.traceback.isBlank()) "${e.type}: ${e.message}\n" else "${e.type}: ${e.message}\n"
    }

    private fun firstLine(text: String): String =
        text.lineSequence().firstOrNull { it.isNotBlank() }?.trim()?.take(160) ?: "错误"

    private fun truncate(text: String): String =
        if (text.length > MAX_OUTPUT) "[输出过长已截断]\n" + text.takeLast(MAX_OUTPUT) else text

    private fun snapshot(globals: Globals, before: Set<String>): List<VarInfo> {
        val items = mutableListOf<VarInfo>()
        val keys = globals.keys()
        for (i in keys.indices.reversed()) {
            if (items.size >= MAX_VARS) break
            val name = keys[i].tojstring()
            if (name in before) continue
            val value = globals.get(name)
            if (value.isnil() || value.isfunction()) continue
            val rendered = value.tojstring()
            items.add(
                VarInfo(
                    name,
                    value.typename(),
                    if (rendered.length > MAX_REPR) rendered.take(MAX_REPR) + "…" else rendered
                )
            )
        }
        return items
    }
}
