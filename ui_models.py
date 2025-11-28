from enum import Enum
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Union,
    Literal,
    Iterable,
    Sequence,
    Tuple,
    IO,
)
from pydantic import BaseModel, Field
import decimal


BadgeColor = Literal[
    "red",
    "orange",
    "yellow",
    "blue",
    "green",
    "violet",
    "gray",
    "grey",
    "primary",
]

DividerColor = Literal[
    "blue",
    "green",
    "orange",
    "red",
    "violet",
    "yellow",
    "gray",
    "grey",
    "rainbow",
]


TextWidth = Literal["content", "stretch"]

DataFrameWidth = Literal["stretch", "content"]
DataFrameHeight = Literal["auto", "stretch"]

OnSelect = Union[
    Literal["ignore", "rerun"],
    Callable[..., Any],
]

SelectionMode = Literal[
    "single-row",
    "multi-row",
    "single-column",
    "multi-column",
    "single-cell",
    "multi-cell",
]


class HexColor(BaseModel):
    value: str = Field(
        ...,
        description="Hex or named CSS color string (e.g., '#FF00AA', 'red').",
    )


class RGB(BaseModel):
    r: int = Field(..., ge=0, le=255)
    g: int = Field(..., ge=0, le=255)
    b: int = Field(..., ge=0, le=255)


class RGBA(BaseModel):
    r: int = Field(..., ge=0, le=255)
    g: int = Field(..., ge=0, le=255)
    b: int = Field(..., ge=0, le=255)
    a: float = Field(..., ge=0.0, le=1.0)


class RGBFloat(BaseModel):
    r: float = Field(..., ge=0.0, le=1.0)
    g: float = Field(..., ge=0.0, le=1.0)
    b: float = Field(..., ge=0.0, le=1.0)


class RGBAFloat(BaseModel):
    r: float = Field(..., ge=0.0, le=1.0)
    g: float = Field(..., ge=0.0, le=1.0)
    b: float = Field(..., ge=0.0, le=1.0)
    a: float = Field(..., ge=0.0, le=1.0)


ColorType = Union[
    HexColor,
    RGB,
    RGBA,
    RGBFloat,
    RGBAFloat,
]


class TitleComponent(BaseModel):
    body: str = Field(
        ...,
        description=(
            "The text to display as GitHub-flavored Markdown. "
            "Supports the same Markdown directives as st.markdown."
        ),
        example="Welcome to the Dashboard",
    )

    anchor: Optional[Union[str, Literal[False]]] = Field(
        None,
        description=(
            "The anchor name that can be accessed with #anchor in the URL. "
            "If omitted, Streamlit generates an anchor automatically. "
            "If False, the anchor is not shown in the UI."
        ),
        example="welcome",
    )

    help: Optional[str] = Field(
        None,
        description=(
            "An optional tooltip displayed next to the title. "
            "Supports GitHub-flavored Markdown."
        ),
        example="This page shows the main dashboard overview.",
    )

    width: Optional[Union[Literal["stretch", "content"], int]] = Field(
        "stretch",
        description=(
            "The width of the title element. "
            "'stretch' matches the parent container, "
            "'content' matches the content width, "
            "or provide an integer for fixed pixel width."
        ),
        example="stretch",
    )


class HeaderComponent(BaseModel):
    body: str = Field(
        ...,
        description=(
            "The text to display as GitHub-flavored Markdown. "
            "Supports the same syntax as st.markdown."
        ),
        example="# User Profile",
    )

    anchor: Optional[Union[str, Literal[False]]] = Field(
        None,
        description=(
            "Anchor name accessible via #anchor in the URL. "
            "If omitted, Streamlit generates one automatically. "
            "If False, no anchor is shown."
        ),
        example="user-profile",
    )

    help: Optional[str] = Field(
        None,
        description=(
            "Tooltip text shown next to the header. "
            "Supports GitHub-flavored Markdown."
        ),
        example="This section displays user information.",
    )

    divider: Optional[Union[bool, DividerColor]] = Field(
        False,
        description=(
            "Colored divider below the header. "
            "If True, Streamlit cycles through colors for each header. "
            "If a string, sets the divider color directly."
        ),
        example="blue",
    )

    width: Optional[Union[Literal["stretch", "content"], int]] = Field(
        "stretch",
        description=(
            "Width of the header element: 'stretch', 'content', or "
            "an integer representing fixed pixel width."
        ),
        example="stretch",
    )


class SubheaderComponent(BaseModel):
    body: str = Field(
        ...,
        description=(
            "The text to display as GitHub-flavored Markdown. "
            "Supports the same Markdown directives as st.markdown."
        ),
        example="User Activity Overview",
    )

    anchor: Optional[Union[str, Literal[False]]] = Field(
        None,
        description=(
            "Anchor name accessible via #anchor in the URL. "
            "If omitted, Streamlit generates an anchor automatically. "
            "If False, the anchor is not shown in the UI."
        ),
        example="user-activity",
    )

    help: Optional[str] = Field(
        None,
        description=(
            "Tooltip text displayed next to the subheader. "
            "Supports GitHub-flavored Markdown."
        ),
        example="Shows recent user activity metrics.",
    )

    divider: Optional[Union[bool, DividerColor]] = Field(
        False,
        description=(
            "Shows a colored divider below the subheader. "
            "If True, Streamlit cycles through divider colors. "
            "If a string, sets the divider color directly."
        ),
        example="green",
    )

    width: Optional[Union[Literal["stretch", "content"], int]] = Field(
        "stretch",
        description=(
            "Width of the subheader element: 'stretch', 'content', "
            "or a fixed integer pixel width."
        ),
        example="stretch",
    )


class MarkdownComponent(BaseModel):
    body: Any = Field(
        ...,
        description=(
            "The text to display as GitHub-flavored Markdown. "
            "If a non-string is passed, it is automatically converted using str(). "
            "Supports emoji shortcodes (:+1:), Material Symbols (:material/icon:), "
            "Streamlit logo (:streamlit:), typographical symbols, LaTeX ($...$ or $$...$$), "
            "colored text (:blue[text]), colored backgrounds (:red-background[text]), "
            "colored badges (:green-badge[text]), and small text (:small[text])."
        ),
        example="Here is **Markdown** with :blue[text] and $\\alpha + \\beta$",
    )

    unsafe_allow_html: bool = Field(
        False,
        description=(
            "Whether to render raw HTML contained in the body. "
            "If False (default), HTML tags are escaped. "
            "If True, HTML is rendered directly (use with caution)."
        ),
        example=False,
    )

    help: Optional[str] = Field(
        None,
        description=(
            "Tooltip shown next to the Markdown block. "
            "Supports GitHub-flavored Markdown."
        ),
        example="This section uses Markdown for formatting.",
    )

    width: Optional[Union[Literal["stretch", "content"], int]] = Field(
        "stretch",
        description=(
            "Width of the Markdown element: "
            "'stretch' matches the container, "
            "'content' matches the natural content width, "
            "or an integer for fixed pixel width."
        ),
        example="stretch",
    )


class BadgeComponent(BaseModel):
    label: str = Field(
        ...,
        description=(
            "The label displayed inside the badge. Supports a subset of "
            "GitHub-flavored Markdown: bold, italics, strikethrough, inline code. "
            "Directives requiring square brackets are not supported because they "
            "are escaped internally."
        ),
        example="**New** Feature!",
    )

    icon: Optional[str] = Field(
        None,
        description=(
            "Optional icon or emoji displayed next to the label. "
            "Supports: a single-character emoji (e.g. '🔥'), or a Material Symbols "
            "icon specified as ':material/icon_name:'. Emoji shortcodes are not supported."
        ),
        example=":material/thumb_up:",
    )

    color: BadgeColor = Field(
        "blue",
        description=(
            "Badge color. Can be one of: red, orange, yellow, blue, green, violet, "
            "gray/grey, or primary. The 'primary' color uses the app’s theme primaryColor."
        ),
        example="green",
    )

    width: Optional[Union[Literal["content", "stretch"], int]] = Field(
        "content",
        description=(
            "Width of the badge element: 'content' (default), 'stretch', "
            "or a fixed integer pixel width."
        ),
        example="content",
    )


class CaptionComponent(BaseModel):
    body: str = Field(
        ...,
        description=(
            "The text to display as GitHub-flavored Markdown. Supports the same "
            "Markdown directives described in st.markdown, including emoji shortcodes, "
            "typographical symbols, LaTeX, and colored text/backgrounds. "
            "Commonly used for small, descriptive text under elements."
        ),
        example="This chart shows _normalized_ daily activity.",
    )

    unsafe_allow_html: bool = Field(
        False,
        description=(
            "Whether to render raw HTML contained within the caption body. "
            "If False (default), HTML is escaped. "
            "If True, HTML is rendered directly — use cautiously."
        ),
        example=False,
    )

    help: Optional[str] = Field(
        None,
        description=(
            "Tooltip displayed next to the caption. Supports GitHub-flavored Markdown. "
            "If None, no tooltip is shown."
        ),
        example="Additional context about this caption.",
    )

    width: Optional[Union[Literal["stretch", "content"], int]] = Field(
        "stretch",
        description=(
            "Width of the caption element: 'stretch' (default), 'content', "
            "or a fixed integer pixel width."
        ),
        example="stretch",
    )


class Code(BaseModel):
    body: str = Field(
        ..., description="The string to display as code or monospace text."
    )

    language: Optional[str] = Field(
        "python",
        description=(
            "The language the code is written in for syntax highlighting. "
            "If None, the text is displayed as plain monospace text."
        ),
    )

    line_numbers: bool = Field(
        False,
        description="Whether to show line numbers to the left of the code block.",
    )

    wrap_lines: bool = Field(
        False,
        description="Whether long lines should wrap instead of scrolling horizontally.",
    )

    height: Union[Literal["content", "stretch"], int] = Field(
        "content",
        description=(
            "The height of the code block. Can be: "
            '"content" (fits content height), '
            '"stretch" (fills parent container), '
            "or a fixed pixel height as an integer."
        ),
    )

    width: Union[Literal["stretch", "content"], int] = Field(
        "stretch",
        description=(
            "The width of the code block. Can be: "
            '"stretch" (fills parent), '
            '"content" (fits content width), '
            "or a fixed width in pixels."
        ),
    )


class Divider(BaseModel):
    width: Union[Literal["stretch"], int] = Field("stretch")


class Text(BaseModel):
    body: str
    help: Optional[str] = None
    width: Union[TextWidth, int] = "content"


class DataFrameComponent(BaseModel):
    data: Optional[Any] = Field(
        None,
        description=(
            "The data to display. Can be any dataframe-like or collection-like object, "
            "including pandas, Polars, PyArrow, Snowpark, NumPy, Python collections, "
            "or any object implementing .to_pandas() or .to_arrow(). "
            "If None, displays an empty table."
        ),
        example={"col1": [1, 2], "col2": [3, 4]},
    )

    width: Union[DataFrameWidth, int] = Field(
        "stretch",
        description=(
            "The width of the dataframe element. "
            "'stretch' matches the parent container width, "
            "'content' matches the content width, "
            "or provide an integer for a fixed pixel width."
        ),
        example="stretch",
    )

    height: Union[DataFrameHeight, int] = Field(
        "auto",
        description=(
            "The height of the dataframe element. "
            "'auto' shows up to ten rows, "
            "'stretch' expands to fill available vertical space, "
            "or provide an integer for fixed pixel height."
        ),
        example="auto",
    )

    hide_index: Optional[bool] = Field(
        None,
        description=(
            "Whether to hide index column(s). "
            "If None (default), Streamlit determines automatically."
        ),
        example=False,
    )

    column_order: Optional[Iterable[str]] = Field(
        None,
        description=(
            "An ordered list of columns to display. Columns may be omitted or repeated. "
            "Positional indices are not allowed."
        ),
        example=["col2", "col1"],
    )

    key: Optional[str] = Field(
        None,
        description=(
            "A unique key that identifies this element. "
            "Required for enabling selection state storage in Session State."
        ),
        example="users_table",
    )

    row_height: Optional[int] = Field(
        None,
        description=(
            "Height of each row in pixels. If None (default), "
            "Streamlit uses a default height fitting a single line of text."
        ),
        example=28,
    )


class TableComponent(BaseModel):
    data: Optional[Any] = Field(
        None,
        description=(
            "Table data. Supports anything accepted by st.dataframe: "
            "pandas, Polars, Arrow, lists, dicts, sets, DB cursors, etc. "
            "Cells may contain GitHub-Flavored Markdown."
        ),
        example={"name": ["John", "Anna"], "age": [30, 25]},
    )

    border: Union[bool, Literal["horizontal"]] = Field(
        True,
        description=(
            "Whether to show borders around the table. "
            "True = full borders, False = no borders, 'horizontal' = row separators only."
        ),
        example=True,
    )


class MetricComponent(BaseModel):
    label: str = Field(
        ...,
        description=(
            "The header or title for the metric. Supports limited GitHub-flavored Markdown "
            "(bold, italics, strikethrough, inline code, links, images). "
            "Unsupported Markdown elements are unwrapped unless escaped."
        ),
        example="Total Sales",
    )

    value: Optional[Union[int, float, decimal.Decimal, str]] = Field(
        ...,
        description=(
            "The value displayed by the metric. `None` renders as a long dash."
        ),
        example=1523,
    )

    delta: Optional[Union[int, float, decimal.Decimal, str]] = Field(
        None,
        description=(
            "Change indicator shown below the metric. Negative values or values starting "
            "with '-' show a downward red arrow. If None, delta is hidden."
        ),
        example="+12%",
    )

    delta_color: Literal["normal", "inverse", "off"] = Field(
        "normal",
        description=(
            "'normal' = red when negative, green when positive. "
            "'inverse' = red when positive, green when negative. "
            "'off' = always gray."
        ),
        example="normal",
    )

    help: Optional[str] = Field(
        None,
        description=(
            "Optional tooltip displayed next to the label. "
            "Only displayed when label_visibility='visible'. "
            "Supports the Markdown directives accepted by st.markdown."
        ),
        example="Total sales recorded for this month.",
    )

    label_visibility: Literal["visible", "hidden", "collapsed"] = Field(
        "visible",
        description=(
            "'visible' = show label. "
            "'hidden' = hide label, but keep a spacer for alignment. "
            "'collapsed' = remove label and spacer."
        ),
        example="visible",
    )

    border: bool = Field(
        False,
        description="Show a border around the metric container.",
        example=False,
    )

    height: Optional[Union[Literal["content", "stretch"], int]] = Field(
        "content",
        description=(
            "Height of the metric container. "
            "'content' = fit to content. 'stretch' = fill available vertical space. "
            "Or specify a fixed pixel height with scrolling if needed."
        ),
        example="content",
    )

    width: Optional[Union[Literal["stretch", "content"], int]] = Field(
        "stretch",
        description=(
            "Width of the metric container. "
            "'stretch' = match parent container. "
            "'content' = fit content width. "
            "Or provide pixel width."
        ),
        example="stretch",
    )

    chart_data: Optional[Iterable] = Field(
        None,
        description=(
            "Optional sparkline data. Any iterable supported by st.dataframe. "
            "If a dataframe-like object is provided, the first column is used."
        ),
        example=[1, 2, 3, 2, 5],
    )

    chart_type: Literal["line", "bar", "area"] = Field(
        "line",
        description=("Type of sparkline chart displayed: line, bar, or area."),
        example="line",
    )


class AreaChartComponent(BaseModel):
    data: Optional[Any] = Field(
        None,
        description="Data to plot. Anything supported by st.dataframe.",
        example=None,
    )

    x: Optional[str] = Field(
        None,
        description=(
            "Column name used for the x-axis. If None, the dataframe index is used."
        ),
        example="date",
    )

    y: Optional[Union[str, Sequence[str]]] = Field(
        None,
        description=(
            "Column(s) used for the y-axis. If None, all remaining columns are used. "
            "If a sequence is provided, each column becomes a separate series."
        ),
        example=["revenue", "profit"],
    )

    x_label: Optional[str] = Field(
        None,
        description="Label for the x-axis. If None, derived from x or omitted.",
        example="Date",
    )

    y_label: Optional[str] = Field(
        None,
        description="Label for the y-axis. If None, derived from y or omitted.",
        example="Value",
    )

    color: Optional[
        Union[
            str,
            Tuple,
            Sequence[str],
            Sequence[Tuple],
        ]
    ] = Field(
        None,
        description=(
            "Colors for the series. For 1 series: hex string or RGB/RGBA tuple. "
            "For multiple series (wide format): a sequence of colors matching the "
            "number of y columns. For long format: a column name used to group data "
            "or values that encode colors."
        ),
        example=["#ffaa00", "#00aaff"],
    )

    stack: Optional[Union[bool, Literal["normalize", "center"]]] = Field(
        None,
        description=(
            "Stacking mode. True = additive stack, False = overlapping, "
            "'normalize' = stack normalized to 100%, 'center' = centered baseline."
        ),
        example="normalize",
    )

    width: Optional[Union[Literal["stretch", "content"], int]] = Field(
        "stretch",
        description=(
            "Width of the chart. 'stretch' matches parent container, "
            "'content' matches content width, or specify a pixel width."
        ),
        example="stretch",
    )

    height: Optional[Union[Literal["stretch", "content"], int]] = Field(
        "content",
        description=(
            "Height of the chart. 'content' fits content, 'stretch' fills available "
            "space, or specify a pixel height with scrolling."
        ),
        example="content",
    )


class BarChartComponent(BaseModel):
    data: Optional[Any] = Field(
        None,
        description="Data to be plotted. Supports anything accepted by st.dataframe.",
        example={"year": [2020, 2021], "sales": [100, 150]},
    )

    x: Optional[str] = Field(
        None,
        description="Column name for x-axis. If None, uses index.",
        example="year",
    )

    y: Optional[Union[str, Sequence[str]]] = Field(
        None,
        description="Column(s) for y-axis. If None, uses all remaining columns.",
        example="sales",
    )

    x_label: Optional[str] = Field(
        None,
        description="Label for the x-axis.",
        example="Year",
    )

    y_label: Optional[str] = Field(
        None,
        description="Label for the y-axis.",
        example="Sales",
    )

    color: Optional[
        Union[
            ColorType,
            Sequence[ColorType],
            str,
            Sequence[str],
        ]
    ] = Field(
        None,
        description=(
            "Color configuration. Accepts:\n"
            "- Hex/named color (e.g. '#ffaa00')\n"
            "- RGB/RGBA integer models\n"
            "- RGB/RGBA float models\n"
            "- A list of any of the above\n"
            "- A column name for coloring by data"
        ),
        example="#ffaa00",
    )

    horizontal: bool = Field(
        False,
        description="If True, bars are horizontal instead of vertical.",
        example=False,
    )

    sort: Union[bool, str] = Field(
        True,
        description="Sorting mode for bars: True, False, 'col', or '-col'.",
        example=True,
    )

    stack: Optional[Union[bool, Literal["normalize", "center", "layered"]]] = (
        Field(
            None,
            description="Stacking mode for bars.",
            example=None,
        )
    )

    width: Union[Literal["stretch", "content"], int] = Field(
        "stretch",
        description="Chart width.",
        example="stretch",
    )

    height: Union[Literal["stretch", "content"], int] = Field(
        "content",
        description="Chart height.",
        example="content",
    )


class LineChartModel(BaseModel):
    data: Optional[Any] = Field(
        default=None,
        description="The data to be plotted. Anything supported by st.dataframe.",
    )

    x: Optional[str] = Field(
        default=None,
        description="Column name for x-axis. If None, index is used.",
    )

    y: Optional[Union[str, Sequence[str]]] = Field(
        default=None,
        description=(
            "Column(s) for y-axis. If None, all other columns are used. "
            "If multiple are given, they are melted into long format."
        ),
    )

    x_label: Optional[str] = Field(
        default=None,
        description="Label for x-axis. If None, Streamlit chooses automatically.",
    )

    y_label: Optional[str] = Field(
        default=None,
        description="Label for y-axis. If None, Streamlit chooses automatically.",
    )

    color: Optional[
        Union[ColorType, Sequence[ColorType], str, Sequence[str]]
    ] = Field(
        default=None,
        description=(
            "Color specification. Can be hex/named color, RGB/RGBA model, "
            "float RGB/RGBA model, a list of colors, or a column name."
        ),
    )

    width: Union[Literal["stretch", "content"], int] = Field(
        default="stretch",
        description=(
            'Width of the element: "stretch", "content", or a fixed pixel integer.'
        ),
    )

    height: Union[Literal["content", "stretch"], int] = Field(
        default="content",
        description=(
            'Height of the element: "content", "stretch", or a fixed pixel integer.'
        ),
    )


class ScatterChartModel(BaseModel):
    data: Optional[Any] = Field(
        default=None,
        description="The data to be plotted. Anything supported by st.dataframe.",
    )

    x: Optional[str] = Field(
        default=None,
        description="Column name for x-axis. If None, the dataframe index is used.",
    )

    y: Optional[Union[str, Sequence[str]]] = Field(
        default=None,
        description=(
            "Column(s) for y-axis. If None, all remaining columns are used. "
            "If multiple are provided, Streamlit melts data into long format."
        ),
    )

    x_label: Optional[str] = Field(
        default=None,
        description="Label for x-axis. If None, Streamlit determines automatically.",
    )

    y_label: Optional[str] = Field(
        default=None,
        description="Label for y-axis. If None, Streamlit determines automatically.",
    )

    color: Optional[
        Union[ColorType, Sequence[ColorType], str, Sequence[str]]
    ] = Field(
        default=None,
        description=(
            "Color specification. Can be hex/named color, RGB/RGBA model, "
            "float RGB/RGBA model, a list of colors, or a column name."
        ),
    )

    size: Optional[Union[str, float, int]] = Field(
        default=None,
        description=(
            "Size of the circles. Can be a fixed numeric size (e.g., 100) "
            "or the name of a column that determines size per datapoint."
        ),
    )

    width: Union[Literal["stretch", "content"], int] = Field(
        default="stretch",
        description=(
            'Width of the chart: "stretch", "content", or fixed pixel integer.'
        ),
    )

    height: Union[Literal["content", "stretch"], int] = Field(
        default="content",
        description=(
            'Height of the chart: "content", "stretch", or fixed pixel integer.'
        ),
    )


class Columns(BaseModel):
    spec: Union[int, Iterable[Union[int, float]]] = Field(
        ...,
        description=(
            "Number of columns (int) or iterable specifying relative widths. "
            "Examples: 3 → three equal columns; [0.7, 0.3] → two columns with relative widths."
        ),
    )
    gap: Optional[Literal["small", "medium", "large"]] = Field(
        "small",
        description=(
            "Gap size between columns. 'small' = 1rem, 'medium' = 2rem, "
            "'large' = 4rem, None = no gap."
        ),
    )
    vertical_alignment: Literal["top", "center", "bottom"] = Field(
        "top",
        description="Vertical alignment of content in columns.",
    )
    border: bool = Field(
        False,
        description="Whether to show a border around each column container.",
    )
    width: Union[Literal["stretch"], int] = Field(
        "stretch",
        description=(
            "'stretch' = container width matches parent; "
            "int = fixed pixel width (capped by parent container)."
        ),
    )


class Container(BaseModel):
    border: Optional[bool] = Field(
        None,
        description=(
            "Whether to show a border around the container. "
            "None (default) = border shown if height is fixed, hidden otherwise."
        ),
    )
    key: Optional[str] = Field(
        None,
        description=(
            "Optional unique key. If provided, also becomes a CSS class "
            "prefixed with 'st-key-'."
        ),
    )
    width: Union[Literal["stretch", "content"], int] = Field(
        "stretch",
        description=(
            "'stretch' = match parent width; 'content' = match content width; "
            "int = fixed pixel width (capped by parent container)."
        ),
    )
    height: Union[Literal["content", "stretch"], int] = Field(
        "content",
        description=(
            "'content' = auto height based on content; "
            "'stretch' = match parent or content (whichever is larger); "
            "int = fixed pixel height with scroll if overflow."
        ),
    )
    horizontal: bool = Field(
        False,
        description=(
            "Whether to lay out elements horizontally (True) or vertically (False). "
            "Horizontal mode wraps overflow to next line."
        ),
    )
    horizontal_alignment: Literal["left", "center", "right", "distribute"] = (
        Field(
            "left",
            description=(
                "Horizontal alignment of elements. "
                "'distribute' expands gaps to fill the width. "
                "When horizontal=False, 'distribute' behaves like 'left'."
            ),
        )
    )
    vertical_alignment: Literal["top", "center", "bottom", "distribute"] = (
        Field(
            "top",
            description=(
                "Vertical alignment of elements. "
                "'distribute' expands gaps to fill the height. "
                "When horizontal=True, 'distribute' behaves like 'top'."
            ),
        )
    )
    gap: Optional[Literal["small", "medium", "large"]] = Field(
        "small",
        description=(
            "Gap between elements. 'small' = 1rem, 'medium' = 2rem, "
            "'large' = 4rem, None = no gap. Applies vertically and horizontally."
        ),
    )
