class MarkerFilter:
    def __init__(self) -> None:
        self.buffer = ""
        self.nokb = False

    def feed(self, text: str, final: bool = False) -> str:
        self.buffer += text
        if "<<NOKB>>" in self.buffer:
            self.nokb = True
            self.buffer = self.buffer.replace("<<NOKB>>", "")
        keep = 0
        if not final:
            for length in range(1, min(8, len(self.buffer)) + 1):
                if "<<NOKB>>".startswith(self.buffer[-length:]):
                    keep = length
        result = self.buffer[:-keep] if keep else self.buffer
        self.buffer = self.buffer[-keep:] if keep else ""
        return result
