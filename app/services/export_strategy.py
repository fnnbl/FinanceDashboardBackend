from abc import ABC, abstractmethod
from fastapi.responses import Response


class ExportStrategy(ABC):
    @abstractmethod
    def generate(self, plan_name: str, plan_description: str | None, items: list[dict]) -> bytes:
        pass

    @abstractmethod
    def media_type(self) -> str:
        pass

    @abstractmethod
    def filename(self, plan_name: str) -> str:
        pass


class PDFExportStrategy(ExportStrategy):
    def generate(self, plan_name: str, plan_description: str | None, items: list[dict]) -> bytes:
        from app.services.pdf_export import generate_plan_pdf
        return generate_plan_pdf(plan_name, plan_description, items)

    def media_type(self) -> str:
        return "application/pdf"

    def filename(self, plan_name: str) -> str:
        return f"{plan_name}.pdf"


class ExcelExportStrategy(ExportStrategy):
    def generate(self, plan_name: str, plan_description: str | None, items: list[dict]) -> bytes:
        from app.services.excel_export import generate_plan_excel
        return generate_plan_excel(plan_name, plan_description, items)

    def media_type(self) -> str:
        return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    def filename(self, plan_name: str) -> str:
        return f"{plan_name}.xlsx"


class ExportContext:
    def __init__(self, strategy: ExportStrategy):
        self._strategy = strategy

    def set_strategy(self, strategy: ExportStrategy) -> None:
        self._strategy = strategy

    def build_response(self, plan_name: str, plan_description: str | None, items: list[dict]) -> Response:
        file_bytes = self._strategy.generate(plan_name, plan_description, items)
        return Response(
            content=file_bytes,
            media_type=self._strategy.media_type(),
            headers={"Content-Disposition": f'attachment; filename="{self._strategy.filename(plan_name)}"'},
        )
