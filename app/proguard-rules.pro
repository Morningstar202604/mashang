# ===== Chaquopy（Python 运行时）=====
# Python 通过原生绑定调用 Java，所有 com.chaquo.python 相关类必须保留
-keep class com.chaquo.python.** { *; }
-keep class com.chaquo.python.android.** { *; }
-dontwarn com.chaquo.python.**

# ===== kotlinx.serialization =====
# 插件已自带规则；此处兜底保留序列化注解与生成的 Serializer
-keepattributes *Annotation*, InnerClasses
-keep class kotlinx.serialization.** { *; }
-keepclassmembers class **$$serializer { *; }
-keepclasseswithmembers class ** {
    kotlinx.serialization.KSerializer serializer(...);
}

# ===== Rhino（JavaScript 运行时）=====
# 解释模式 + 宿主函数经匿名 BaseFunction 子类注入脚本作用域，
# 混淆会破坏 Rhino 内部的反射与 SecurityController 初始化。
# keep 范围含 org.mozilla.classfile（ClassFileWriter 等）：解释模式虽不编译
# 字节码，但 Rhino 部分路径仍引用该包，R8 裁剪会导致运行时 NoClassDefFoundError
-keep class org.mozilla.** { *; }
-dontwarn org.mozilla.**

# ===== LuaJ（Lua 运行时）=====
# LuaJ 附带的 javax.script 适配器在 Android 上不存在（Android 没有 JSR-223），
# 我们只用 org.luaj.vm2.* 解释器本体，不走 ScriptEngine 路径。
# R8 会在 minifyRelease 时因缺类直接失败（2026-10-24 CI 实测），
# 因此 keep 解释器核心并忽略脚本引擎包的缺失警告。
-keep class org.luaj.vm2.** { *; }
-keep class org.luaj.vm2.lib.** { *; }
-keep class org.luaj.vm2.compiler.** { *; }
-dontwarn org.luaj.vm2.script.**
-dontwarn javax.script.**

# luajc 是 LuaJ 的「AOT 转 JVM 字节码」编译器，依赖 BCEL（org.apache.bcel），
# 而 BCEL 未随依赖引入、Android 上也不可用。我们只用解释执行路径，
# 直接忽略这门编译器相关的缺失类（与 javax.script 同理）。
-dontwarn org.apache.bcel.**
-dontwarn org.luaj.vm2.luajc.**
