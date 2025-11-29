import json
import logging
from typing import Dict, List, Optional, Set, Any
import numpy as np
from src.tool_models import Tool
from sentence_transformers import SentenceTransformer

logger = logging.getLogger("tool_manager")


class ToolManager:
    """Manages tool registration and lazy-loading discovery."""

    def __init__(self):
        self.registry: Dict[str, Dict[str, Any]] = {}
        self.loaded_tools: Set[str] = set()
        self.always_loaded: Set[str] = {
            "search_tools"
        }  # Meta-tool always available

        # Initialize semantic search model
        self.model = None
        self.tool_embeddings = {}

        if SentenceTransformer:
            try:
                self.model = SentenceTransformer("all-MiniLM-L6-v2")
                logger.info(
                    "🧠 Semantic search model loaded: all-MiniLM-L6-v2"
                )
            except Exception as e:
                logger.error(f"❌ Failed to load semantic search model: {e}")
        else:
            logger.warning(
                "⚠️ sentence-transformers not found. Falling back to keyword search."
            )

    def register_tool(
        self,
        name: str,
        tool: Tool,
        keywords: List[str],
        category: str = "general",
        always_load: bool = False,
    ) -> None:
        """
        Register a tool in the registry.

        Args:
            name: Tool name
            tool: Full tool definition
            keywords: Search keywords for discovery
            category: Tool category (ui_management, data_viz, etc.)
            always_load: If True, tool is always loaded (like search_tools)
        """
        self.registry[name] = {
            "definition": tool,
            "keywords": keywords,
            "category": category,
            "description": tool.description,
        }

        if always_load:
            self.always_loaded.add(name)
            self.loaded_tools.add(name)

        # Compute embedding if model is available
        if self.model:
            try:
                # Combine name, description, and keywords for rich context
                text = f"{name}: {tool.description}. Keywords: {', '.join(keywords)}"
                embedding = self.model.encode(text)
                self.tool_embeddings[name] = embedding
            except Exception as e:
                logger.error(f"Failed to compute embedding for {name}: {e}")

        logger.debug(f"Registered tool: {name} (category: {category})")

    def search(
        self, query: str, category: Optional[str] = None, top_k: int = 3
    ) -> str:
        """
        Search for tools matching the query using semantic search if available.

        Args:
            query: Search query (what the user wants to do)
            category: Optional category filter
            top_k: Maximum number of results to return

        Returns:
            JSON string with matching tools
        """
        matches = []

        # Use semantic search if available
        if self.model and self.tool_embeddings:
            try:
                query_embedding = self.model.encode(query)

                # Calculate cosine similarity for all tools
                for name, meta in self.registry.items():
                    # Skip if category filter doesn't match
                    if category and meta["category"] != category:
                        continue

                    if name in self.tool_embeddings:
                        tool_embedding = self.tool_embeddings[name]
                        # Cosine similarity
                        similarity = np.dot(
                            query_embedding, tool_embedding
                        ) / (
                            np.linalg.norm(query_embedding)
                            * np.linalg.norm(tool_embedding)
                        )

                        # Threshold for semantic match (0.3 is usually a good baseline for MiniLM)
                        if similarity > 0.3:
                            matches.append(
                                {
                                    "name": name,
                                    "description": meta["description"],
                                    "category": meta["category"],
                                    "score": float(similarity),
                                }
                            )
            except Exception as e:
                logger.error(f"Semantic search failed: {e}")
                # Fallback to keyword search will happen if matches is empty

        # Fallback to keyword search if semantic search failed or returned no results
        if not matches:
            logger.info("Falling back to keyword search")
            query_lower = query.lower()
            query_words = [w for w in query_lower.split() if len(w) > 3]

            for name, meta in self.registry.items():
                if category and meta["category"] != category:
                    continue

                score = 0
                for keyword in meta["keywords"]:
                    if keyword.lower() in query_lower:
                        score += 1.0

                if query_words:
                    if any(
                        word in meta["description"].lower()
                        for word in query_words
                    ):
                        score += 0.5

                if score > 0:
                    matches.append(
                        {
                            "name": name,
                            "description": meta["description"],
                            "category": meta["category"],
                            "score": score,
                        }
                    )

        # Sort by score and limit results
        matches.sort(key=lambda x: x["score"], reverse=True)
        results = matches[:top_k]

        # Auto-load tools with high confidence
        # For semantic search, >0.4 is a strong match
        # For keyword search, >=1.0 is a strong match
        threshold = 0.4 if (self.model and self.tool_embeddings) else 1.0
        tools_to_load = [m["name"] for m in results if m["score"] >= threshold]

        if tools_to_load:
            self.load_tools(tools_to_load)
            logger.info(
                f"🔍 Found and loaded {len(tools_to_load)} tools: {tools_to_load}"
            )
        elif results:
            logger.info(
                f"🔍 Found {len(results)} tools but none met threshold >= {threshold} for auto-loading"
            )

        return json.dumps(results, indent=2)

    def load_tools(self, tool_names: List[str]) -> None:
        """Load specific tools into active context."""
        for name in tool_names:
            if name in self.registry:
                self.loaded_tools.add(name)
                logger.debug(f"Loaded tool: {name}")

    def unload_tools(self, tool_names: List[str]) -> None:
        """Unload tools from active context (except always_loaded)."""
        for name in tool_names:
            if name not in self.always_loaded:
                self.loaded_tools.discard(name)
                logger.debug(f"Unloaded tool: {name}")

    def get_active_tools(self) -> List[Tool]:
        """Get currently loaded tool definitions."""
        tools = []
        for name in self.loaded_tools:
            if name in self.registry:
                tools.append(self.registry[name]["definition"])
        return tools

    def get_search_tool(self) -> Tool:
        """Get the search_tools meta-tool definition."""
        return Tool(
            name="search_tools",
            description="Search for and load tools by describing what you want to do. After searching, the matching tools will be automatically loaded and available for immediate use in your next action. You should search for tools and then use them in the same conversation turn when possible.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "What you want to do (e.g., 'create a page', 'update layout', 'add chart')",
                    },
                    "category": {
                        "type": "string",
                        "enum": ["ui_management", "data_viz", "general"],
                        "description": "Optional category filter",
                    },
                },
                "required": ["query"],
                "additionalProperties": False,
            },
            strict=True,
        )

    def clear_loaded_tools(self) -> None:
        """Clear all loaded tools except always_loaded ones."""
        self.loaded_tools = self.always_loaded.copy()
        logger.info("Cleared loaded tools, keeping always-loaded tools")

    def get_stats(self) -> Dict[str, int]:
        """Get statistics about tool usage."""
        return {
            "total_registered": len(self.registry),
            "currently_loaded": len(self.loaded_tools),
            "always_loaded": len(self.always_loaded),
            "semantic_search_enabled": self.model is not None,
        }
