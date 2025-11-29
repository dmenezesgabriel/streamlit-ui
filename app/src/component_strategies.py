from abc import ABC, abstractmethod
from typing import Union
import streamlit as st
import json
import pandas as pd
import logging

from src.models import UIComponent, LayoutComponent, ComponentType, LayoutType

logger = logging.getLogger("component_strategies")


class ComponentRenderStrategy(ABC):
    @abstractmethod
    def render(self, component: UIComponent) -> None:
        pass


class TextStrategy(ComponentRenderStrategy):
    def render(self, component: UIComponent) -> None:
        st.write(component.data)


class MarkdownStrategy(ComponentRenderStrategy):
    def render(self, component: UIComponent) -> None:
        st.markdown(component.data)


class HeaderStrategy(ComponentRenderStrategy):
    def render(self, component: UIComponent) -> None:
        st.header(component.data)


class SubheaderStrategy(ComponentRenderStrategy):
    def render(self, component: UIComponent) -> None:
        st.subheader(component.data)


class CodeStrategy(ComponentRenderStrategy):
    def render(self, component: UIComponent) -> None:
        st.code(
            component.data, language=component.props.get("language", "python")
        )


class DataFrameStrategy(ComponentRenderStrategy):
    def render(self, component: UIComponent) -> None:
        data = component.data

        # Guard: If data is not a string, render directly
        if not isinstance(data, str):
            st.dataframe(data)
            return

        # Try to parse JSON string
        try:
            parsed = json.loads(data)
            df = self._create_dataframe(parsed)
            st.dataframe(df)
        except Exception as e:
            logger.error(f"Failed to parse dataframe data: {e}")
            st.error(f"Invalid dataframe data: {e}")
            st.code(data)

    @staticmethod
    def _create_dataframe(parsed: dict) -> pd.DataFrame:
        if isinstance(parsed, dict) and "data" in parsed:
            return pd.DataFrame(
                parsed["data"], columns=parsed.get("columns", None)
            )
        return pd.DataFrame(parsed)


class BarChartStrategy(ComponentRenderStrategy):
    def render(self, component: UIComponent) -> None:
        data = component.data

        if not isinstance(data, str):
            st.bar_chart(data)
            return

        try:
            parsed = json.loads(data)
            df = self._create_dataframe(parsed)
            st.bar_chart(df)
        except Exception as e:
            logger.error(f"Failed to parse bar chart data: {e}")
            st.error(f"Invalid bar chart data: {e}")

    @staticmethod
    def _create_dataframe(parsed: dict) -> pd.DataFrame:
        if isinstance(parsed, dict) and "data" in parsed:
            return pd.DataFrame(
                parsed["data"], columns=parsed.get("columns", None)
            )
        return pd.DataFrame(parsed)


class LineChartStrategy(ComponentRenderStrategy):
    def render(self, component: UIComponent) -> None:
        data = component.data

        if not isinstance(data, str):
            st.line_chart(data)
            return

        try:
            parsed = json.loads(data)
            df = self._create_dataframe(parsed)
            st.line_chart(df)
        except Exception as e:
            logger.error(f"Failed to parse line chart data: {e}")
            st.error(f"Invalid line chart data: {e}")

    @staticmethod
    def _create_dataframe(parsed: dict) -> pd.DataFrame:
        """Create DataFrame from parsed JSON data."""
        if isinstance(parsed, dict) and "data" in parsed:
            return pd.DataFrame(
                parsed["data"], columns=parsed.get("columns", None)
            )
        return pd.DataFrame(parsed)


class MetricStrategy(ComponentRenderStrategy):
    def render(self, component: UIComponent) -> None:
        st.metric(
            label=component.props.get("label", ""),
            value=component.data,
        )


class ComponentStrategyFactory:
    _strategies = {
        ComponentType.TEXT: TextStrategy(),
        ComponentType.MARKDOWN: MarkdownStrategy(),
        ComponentType.HEADER: HeaderStrategy(),
        ComponentType.SUBHEADER: SubheaderStrategy(),
        ComponentType.CODE: CodeStrategy(),
        ComponentType.DATAFRAME: DataFrameStrategy(),
        ComponentType.BAR_CHART: BarChartStrategy(),
        ComponentType.LINE_CHART: LineChartStrategy(),
        ComponentType.METRIC: MetricStrategy(),
    }

    @classmethod
    def get_strategy(
        cls, component_type: ComponentType
    ) -> ComponentRenderStrategy:

        strategy = cls._strategies.get(component_type)

        if strategy is None:
            raise ValueError(
                f"No rendering strategy found for component type: {component_type}"
            )

        return strategy

    @classmethod
    def register_strategy(
        cls, component_type: ComponentType, strategy: ComponentRenderStrategy
    ) -> None:
        cls._strategies[component_type] = strategy
