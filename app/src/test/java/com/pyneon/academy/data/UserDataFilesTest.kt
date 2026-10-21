package com.pyneon.academy.data

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder
import java.io.File

class UserDataFilesTest {

    @get:Rule
    val tmp = TemporaryFolder()

    @Test
    fun deletesEveryUserDataFile() {
        val dir = tmp.newFolder()
        UserDataFiles.names.forEach { File(dir, it).writeText("x") }

        val failures = UserDataFiles.deleteAll(dir)

        assertTrue("no failures expected, got $failures", failures.isEmpty())
        UserDataFiles.names.forEach { name ->
            assertTrue("$name should be gone", !File(dir, name).exists())
        }
    }

    @Test
    fun keepsUnrelatedFiles() {
        val dir = tmp.newFolder()
        val sentinel = File(dir, "pyneon_progress.preferences_pb").apply { writeText("keep") }
        UserDataFiles.names.forEach { File(dir, it).writeText("x") }

        UserDataFiles.deleteAll(dir)

        assertTrue("unrelated file must survive", sentinel.exists())
        assertEquals("keep", sentinel.readText())
    }

    @Test
    fun idempotentWhenFilesMissing() {
        val dir = tmp.newFolder()
        assertTrue(UserDataFiles.deleteAll(dir).isEmpty())
        assertTrue(UserDataFiles.deleteAll(dir).isEmpty())
    }

    @Test
    fun coversExactlyTheBackedUpFiles() {
        assertEquals(
            listOf("pyneon_mistakes.json", "pyneon_review_cards.json"),
            UserDataFiles.names,
        )
    }
}
