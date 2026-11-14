import json
import sys
from io import TextIOWrapper
from pathlib import Path
from typing import cast

from app.main import app
from app.modules.workspace import schemas


def export() -> dict[str, object]:
    result = app.openapi()
    for cls in (schemas.DeltaEvent, schemas.LeadPromptEvent, schemas.DoneEvent, schemas.ErrorEvent):
        result["components"]["schemas"][cls.__name__] = cls.model_json_schema()
    return dict(result)


if __name__ == "__main__":
    text = json.dumps(export(), ensure_ascii=False, indent=2) + "\n"
    if len(sys.argv) > 1:
        Path(sys.argv[1]).write_text(text, encoding="utf-8")
    else:
        cast(TextIOWrapper, sys.stdout).reconfigure(encoding="utf-8")
        sys.stdout.write(text)
