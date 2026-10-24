package com.pyneon.academy.screens

import androidx.compose.runtime.Composable

/**
 * 兼容入口：旧导航名 `contenthub` 指向语言中心。
 *
 * 2026-10-24 起课程包统一下载入口是 [LanguageCenterScreen]；这里只保留
 * 一个转发函数，避免两套下载 UI 各自维护、状态不一致。
 */
@Composable
fun ContentHubScreen(onBack: () -> Unit) = LanguageCenterScreen(onBack = onBack)
