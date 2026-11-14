"""Strip an internal marker even when a provider splits it across chunks."""

MARKER = "<<NOKB>>"


class NOKBFilter:
    def __init__(self) -> None:
        self.pending = ""
        self.nokb = False

    def feed(self, text: str) -> str:
        self.pending += text
        if MARKER in self.pending:
            self.nokb = True
            self.pending = self.pending.replace(MARKER, "")
        keep = 0
        for length in range(1, len(MARKER)):
            if self.pending.endswith(MARKER[:length]):
                keep = length
        if keep:
            output, self.pending = self.pending[:-keep], self.pending[-keep:]
        else:
            output, self.pending = self.pending, ""
        return output

    def finish(self) -> str:
        # A dangling marker prefix is not customer-facing text.
        self.pending = ""
        return ""
