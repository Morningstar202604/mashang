package com.pyneon.academy.data

import com.pyneon.academy.utils.UpdateChecker

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

/** 版本比较：只用于「检查更新」按钮，不能把降级或垃圾字符串判成新版本。 */
class UpdateCheckerTest {

    @Test
    fun newerPatchIsDetected() {
        assertTrue(UpdateChecker.isNewer("0.4.1", "0.4.0"))
        assertTrue(UpdateChecker.isNewer("v0.5.0", "0.4.9"))
        assertTrue(UpdateChecker.isNewer("1.0", "0.9.9"))
    }

    @Test
    fun sameOrOlderIsNotNewer() {
        assertFalse(UpdateChecker.isNewer("0.4.0", "0.4.0"))
        assertFalse(UpdateChecker.isNewer("0.3.9", "0.4.0"))
        assertFalse(UpdateChecker.isNewer("v0.4.0", "0.4"))
    }

    @Test
    fun malformedInputNeverClaimsUpdate() {
        assertFalse(UpdateChecker.isNewer("", "0.4.0"))
        assertFalse(UpdateChecker.isNewer("latest", "0.4.0"))
        assertFalse(UpdateChecker.isNewer("0.4.x", "0.4.0"))
    }
}
