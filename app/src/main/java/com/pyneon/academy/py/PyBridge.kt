package com.pyneon.academy.py

import android.content.Context
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform
import com.pyneon.academy.lang.LanguageIds
import com.pyneon.academy.lang.LanguageRuntime
import com.pyneon.academy.lang.RunResult
import com.pyneon.academy.lang.VarInfo
import org.json.JSONArray
import org.json.JSONObject

/**
 * Python 运行时（Chaquopy 内嵌 CPython）。
 *
 * 多语言架构下它是 [LanguageRuntime] 的首个实现：UI 与判题逻辑只依赖接口，
 * 新增 JavaScript / Java 等语言时新增实现类并注册进 LanguageRegistry 即可，
 * 本文件之外的调用方无需改动。
 */
object PyBridge : LanguageRuntime {

    override val id: String = LanguageIds.PYTHON
    override val displayName: String = "Python"
    override val fileExtension: String = "py"
    override val grammarScope: String = "source.python"

    @Volatile
    private var started = false

    override val version: String
        get() = pythonVersion()

    override fun isAvailable(): Boolean = started || Python.isStarted()

    override fun ensureStarted(context: Context) {
        if (started) return
        synchronized(this) {
            if (!started && !Python.isStarted()) {
                Python.start(AndroidPlatform(context.applicationContext))
                started = true
            }
        }
    }

    private fun module(name: String) = Python.getInstance().getModule(name)

    override fun runCode(
        code: String,
        stdinLines: List<String>,
        timeoutSec: Double
    ): RunResult {
        val payload = JSONObject().apply {
            put("code", code)
            put("stdin", JSONArray(stdinLines))
            put("timeout", timeoutSec)
        }
        return parseRun(module("runner").callAttr("run_code_json", payload.toString()).toString())
    }

    override fun checkExercise(
        code: String,
        tests: List<String>,
        stdinLines: List<String>
    ): RunResult {
        val payload = JSONObject().apply {
            put("code", code)
            put("tests", JSONArray(tests))
            put("stdin", JSONArray(stdinLines))
        }
        return parseRun(module("runner").callAttr("check_exercise_json", payload.toString()).toString())
    }

    fun pythonVersion(): String {
        return try {
            val obj = JSONObject(module("runner").callAttr("info_json").toString())
            obj.optString("python_version", "3.x")
        } catch (_: Throwable) {
            "3.x"
        }
    }

    override fun warmup(): Boolean {
        return try {
            runCode("pass", emptyList(), 6.0).ok
        } catch (_: Throwable) {
            false
        }
    }

    override fun replStart() {
        module("repl").callAttr("start")
    }

    override fun replPush(line: String): Pair<Boolean, String> {
        val obj = JSONObject(module("repl").callAttr("push", line).toString())
        return obj.getBoolean("more") to obj.getString("output")
    }

    private fun parseRun(raw: String): RunResult {
        val obj = JSONObject(raw)
        val errorObj = obj.optJSONObject("error")
        val varsJson = obj.optJSONArray("variables") ?: JSONArray()
        val vars = buildList {
            for (i in 0 until varsJson.length()) {
                val v = varsJson.getJSONObject(i)
                add(VarInfo(v.getString("name"), v.getString("type"), v.getString("value")))
            }
        }
        return RunResult(
            ok = obj.getBoolean("ok"),
            stdout = obj.optString("stdout"),
            stderr = obj.optString("stderr"),
            errorType = errorObj?.optString("type")?.ifEmpty { null },
            errorMessage = errorObj?.optString("message")?.ifEmpty { null },
            traceback = errorObj?.optString("traceback")?.ifEmpty { null },
            durationMs = obj.optLong("duration_ms"),
            variables = vars,
            passed = if (obj.has("passed") && !obj.isNull("passed")) obj.getBoolean("passed") else null
        )
    }
}
