package cn.aicardhub.nfc.core

import org.junit.Assert.*
import org.junit.Test
import java.net.URI

class TrustedLinksTest {
    private val links = TrustedLinks("https://cards.example.test/aicardhub/")
    private fun reject(value: String) { assertThrows(Exception::class.java) { links.parse(value) } }
    @Test fun rootAndPrefixBuildExactUrls() {
        val request = links.parse("https://cards.example.test/aicardhub/share/nfc?code=abc_12&mode=emulate&e=7")
        assertEquals("https://cards.example.test/aicardhub/c/abc_12?s=nfc&e=7", links.shortUrl(request))
        assertEquals("https://cards.example.test/aicardhub/c/abc_12?s=link&e=7", links.normalShareUrl(request))
        assertEquals("https://cards.example.test/aicardhub/api/v1/public/cards/abc_12?e=7", links.previewUrl(request).toString())
        assertEquals("https://cards.example.test/c/a?s=nfc", TrustedLinks("https://cards.example.test").shortUrl(ImportRequest("a", ImportMode.EMULATE, null)))
    }
    @Test fun shortLinkAcceptedWithoutChangingOrigin() {
        assertEquals("abc", links.parse("https://cards.example.test/aicardhub/c/abc?s=nfc").code)
        assertEquals("abc", links.parse("https://CARDS.EXAMPLE.TEST/aicardhub/c/abc?s=nfc").code)
    }
    @Test fun writeIsSuggestionAndRejectsCampaign() {
        assertEquals(ImportMode.WRITE, links.parse("https://cards.example.test/aicardhub/share/nfc?code=a&mode=write").mode)
        reject("https://cards.example.test/aicardhub/share/nfc?code=a&mode=write&e=1")
    }
    @Test fun rejectExternalAndCredentialOrigins() {
        listOf("http://cards.example.test", "https://cards.example.test.evil.test", "https://evil.test",
            "https://user@cards.example.test", "https://cards.example.test:443").forEach { reject("$it/aicardhub/c/a?s=nfc") }
    }
    @Test fun rejectWrongPathsAndTraversal() {
        listOf("/c/a", "/aicardhub/card/a", "/aicardhub/c/a/b", "/aicardhub/c/../a", "/aicardhub/c/%2F", "/aicardhub/c/%252F",
            "/aicardhub/c/%2e%2e", "/aicardhub//c/a", "/aicardhub/share/nfc/extra").forEach { reject("https://cards.example.test$it?s=nfc") }
    }
    @Test fun rejectDuplicateUnknownAndMalformedParameters() {
        listOf("code=a&code=b", "code=a&mode=bad", "code=a&url=https%3A%2F%2Fevil.test", "code=a&e=0", "code=a&e=-1",
            "code=a&e=9223372036854775808", "code=a&e=01", "code=%252f", "code=%2f", "code=a%26b", "code=a+z", "code=a#fragment",
            "code=a&token=secret", "code=${"a".repeat(33)}", "code=a&%63ode=b").forEach {
            reject("https://cards.example.test/aicardhub/share/nfc?$it")
        }
        reject("https://cards.example.test/aicardhub/c/a?s=link")
    }
    @Test fun decodeExactlyOnceAndRedirectsStayOnExactPreview() {
        assertEquals("abc", links.parse("https://cards.example.test/aicardhub/share/nfc?code=%61bc").code)
        val request = ImportRequest("abc", ImportMode.EMULATE, 1)
        assertTrue(links.isAllowedPreviewRedirect(links.previewUrl(request), request))
        assertFalse(links.isAllowedPreviewRedirect(URI("https://evil.test/aicardhub/api/v1/public/cards/abc?e=1"), request))
        assertFalse(links.isAllowedPreviewRedirect(URI("https://cards.example.test/aicardhub/api/v1/public/cards/other?e=1"), request))
        assertFalse(links.isAllowedPreviewRedirect(URI("https://cards.example.test/aicardhub/api/v1/public/cards/abc?e=2"), request))
    }
}
