package com.pyneon.academy.lang.lua

import com.pyneon.academy.lua.LuaBridge
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Lua 运行时行为锁（纯 JVM，不需要 Android 设备）。
 *
 * 锁定四类真实风险：
 *  R1 正常执行与 print 输出；
 *  R2 死循环必须被指令钩子中断，不能拖死进程；
 *  R3 沙箱边界：io / os / luajava / require 外部文件全部不可用；
 *  R4 判题语义：assert 失败可读、变量快照只列新变量。
 */
class LuaSandboxTest {

    @Test
    fun executesBasicCodeAndCapturesPrint() {
        val r = LuaBridge.runCode(
            "local s = 0\nfor i = 1, 10 do s = s + i end\nprint('sum', s)\nprint(string.upper('ok'))",
            emptyList(),
            5.0
        )
        assertTrue(r.ok)
        assertEquals("sum\t55\nOK\n", r.stdout)
    }

    @Test
    fun infiniteLoopIsInterrupted() {
        val started = System.currentTimeMillis()
        val r = LuaBridge.runCode("while true do end", emptyList(), 0.5)
        val elapsed = System.currentTimeMillis() - started
        assertFalse(r.ok)
        assertEquals("Timeout", r.errorType)
        assertTrue("看门狗应立即中断，实际 ${elapsed}ms", elapsed < 5000)
    }

    @Test
    fun sandboxBlocksFilesystemAndJavaInterop() {
        for (probe in listOf(
            "print(type(io))",
            "print(type(os))",
            "print(type(luajava))",
            "print(loadfile('/etc/passwd'))",
            "print(dofile('/etc/passwd'))"
        )) {
            val r = LuaBridge.runCode(probe, emptyList(), 3.0)
            assertTrue("$probe 不应产生文件内容：${r.stdout}", !r.stdout.contains("root:"))
        }
        val io = LuaBridge.runCode("print(type(io))", emptyList(), 3.0)
        assertEquals("nil\n", io.stdout)
    }

    @Test
    fun checkExercisePassesAndReportsFirstFailure() {
        val ok = LuaBridge.checkExercise(
            "function add(a, b) return a + b end",
            listOf("assert(add(1, 2) == 3, 'add failed')")
        )
        assertTrue(ok.ok)
        assertEquals(true, ok.passed)

        val bad = LuaBridge.checkExercise(
            "function add(a, b) return a - b end",
            listOf("assert(add(1, 2) == 3, 'add(1,2) 应为 3')")
        )
        assertEquals(false, bad.passed)
        assertEquals("TestFailed", bad.errorType)
        assertTrue(bad.errorMessage!!.contains("add(1,2) 应为 3"))
    }

    @Test
    fun syntaxErrorIsReportedNotThrown() {
        val r = LuaBridge.runCode("if true then\nprint('x')\n", emptyList(), 3.0)
        assertFalse(r.ok)
        assertNotNull(r.errorType)
        assertTrue(r.errorMessage!!.isNotBlank())
    }

    @Test
    fun variableSnapshotOnlyShowsNewValues() {
        val r = LuaBridge.runCode(
            "local hidden = 1\nvisible = 'v'\nnumbers = {1, 2, 3}",
            emptyList(),
            3.0
        )
        assertTrue(r.ok)
        val names = r.variables.map { it.name }
        assertTrue("应包含 visible，实际 $names", names.contains("visible"))
        assertTrue("应包含 numbers，实际 $names", names.contains("numbers"))
        assertFalse("局部变量不应出现在快照，实际 $names", names.contains("hidden"))
    }

    @Test
    fun replKeepsStateAcrossLines() {
        LuaBridge.replStart()
        val first = LuaBridge.replPush("x = 41")
        assertEquals(false, first.first)
        val second = LuaBridge.replPush("print(x + 1)")
        assertEquals(false, second.first)
        assertEquals("42\n", second.second)
        LuaBridge.replStart()
    }

    @Test
    fun replWaitsForIncompleteBlock() {
        LuaBridge.replStart()
        val more = LuaBridge.replPush("if true then")
        assertEquals(true, more.first)
        val done = LuaBridge.replPush("print('inside')\nend")
        assertEquals(false, done.first)
        assertTrue(done.second.contains("inside"))
        LuaBridge.replStart()
    }
}
