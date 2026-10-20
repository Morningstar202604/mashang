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
