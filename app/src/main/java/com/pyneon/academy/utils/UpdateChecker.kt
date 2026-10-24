package com.pyneon.academy.utils

import android.content.Context
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL

/**
 * 手动检查更新：只读取 GitHub Releases 的公开 latest 接口（无账号、无设备信息）。
 *
 * 应用本身没有自动更新（不申请安装未知来源权限、不静默下载），这里只做
 * 「告诉你有没有新版本 + 给一个下载链接」；失败时静默降级为「无法检查」，
 * 绝不阻塞离线学习。
 */
object UpdateChecker {

    data class ReleaseInfo(
        val version: String,
        val url: String,
        val publishedAt: String
    )

    private const val API = "https://api.github.com/repos/badhope/mashang/releases/latest"

    suspend fun fetchLatest(): Result<ReleaseInfo> = withContext(Dispatchers.IO) {
        try {
            val conn = (URL(API).openConnection() as HttpURLConnection).apply {
                connectTimeout = 6000
                readTimeout = 6000
                requestMethod = "GET"
                setRequestProperty("Accept", "application/vnd.github+json")
                setRequestProperty("User-Agent", "Mashang-Android")
            }
            try {
                if (conn.responseCode != 200) {
                    return@withContext Result.failure(IllegalStateException("HTTP ${conn.responseCode}"))
                }
                val body = conn.inputStream.bufferedReader().use { it.readText() }
                val json = JSONObject(body)
                val tag = json.optString("tag_name").trim().removePrefix("v")
                val url = json.optString("html_url")
                if (tag.isBlank() || url.isBlank()) {
                    return@withContext Result.failure(IllegalStateException("返回内容缺少版本信息"))
                }
                Result.success(ReleaseInfo(tag, url, json.optString("published_at")))
            } finally {
                conn.disconnect()
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    /** 语义化比较：返回 latest 是否比 current 新。非法输入按「不更新」处理。 */
    fun isNewer(latest: String, current: String): Boolean {
        fun parse(v: String): List<Int>? =
            v.trim().removePrefix("v").split('.').map { it.toIntOrNull() ?: return null }
        val a = parse(latest) ?: return false
        val b = parse(current) ?: return false
        for (i in 0 until maxOf(a.size, b.size)) {
            val x = a.getOrElse(i) { 0 }
            val y = b.getOrElse(i) { 0 }
            if (x != y) return x > y
        }
        return false
    }
}
