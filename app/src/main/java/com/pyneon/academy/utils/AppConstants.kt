package com.pyneon.academy.utils

import com.pyneon.academy.BuildConfig

/**
 * 应用全局常量
 */
object AppConstants {
    // 版本信息（单一来源：由 build.gradle.kts 生成 BuildConfig，发版只改 gradle）
    val VERSION_NAME: String = BuildConfig.VERSION_NAME
    val VERSION_CODE: Int = BuildConfig.VERSION_CODE
    
    // 应用名称（2026-10 品牌重塑：去除 Python 专属命名，扩展为多语言学习终端）
    const val APP_NAME = "码上"
    // APP_NAME_CN 用作「码上（X）」里的括号内容，与 APP_NAME 相同会导致
    // 「码上（码上）」这类重复品牌；中文名已在 APP_NAME，这里用英文名。
    const val APP_NAME_CN = "Mashang"
    const val APP_NAME_EN = "Mashang"
    
    // 项目主页（GitCode 主仓）
    const val REPO_URL = "https://gitcode.com/badhope/mashang-python"

    // 分享标签（2026-10 品牌重塑：PY_NOW 已退役，统一为「码上 / Mashang」）
    const val SHARE_HASHTAG = "#码上 #Mashang #编程学习"

    // ===== 法律主体与合规信息（上架前请将占位符替换为实名信息）=====
    // 上架开发者/运营者名称（华为应用市场公开显示）
    const val DEV_NAME = "bigbad"

    // 隐私事务联系邮箱
    const val CONTACT_EMAIL = "bigbad338@outlook.com"

    // 注：开发者地址/客服信息在华为开发者后台填写并公开展示，无需在本仓库硬编码。

    // 隐私政策与用户协议（托管于 GitCode 主仓，可作为应用市场隐私政策 URL）
    const val PRIVACY_POLICY_URL =
        "https://gitcode.com/badhope/mashang-python/blob/main/PRIVACY_POLICY.md"
    const val TERMS_URL =
        "https://gitcode.com/badhope/mashang-python/blob/main/TERMS_OF_SERVICE.md"
}
