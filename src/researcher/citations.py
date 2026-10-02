from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from .schemas import SourceRecord


@dataclass(frozen=True)
class CitationEdge:
    source_doi: str
    target_doi: str
    relation: str = "cites"


@dataclass
class CitationGraph:
    nodes: dict[str, SourceRecord]
    edges: list[CitationEdge]

    def neighbors(self, doi: str) -> list[SourceRecord]:
        target_dois = {
            edge.target_doi
            for edge in self.edges
            if edge.source_doi == doi
        }
        return [self.nodes[item] for item in target_dois if item in self.nodes]

    def cited_by(self, doi: str) -> list[SourceRecord]:
        source_dois = {
            edge.source_doi
            for edge in self.edges
            if edge.target_doi == doi
        }
        return [self.nodes[item] for item in source_dois if item in self.nodes]


class CitationGraphBuilder:
    """Builds a graph from resolved DOI relationships.

    Retrieval of citation relationships is intentionally separate so provider
    adapters can be replaced without changing the graph representation.
    """

    def build(self, records: list[SourceRecord],
              relationships: list[tuple[str, str]]) -> CitationGraph:
        nodes = {
            record.doi: record
            for record in records
            if record.doi
        }
        edges: list[CitationEdge] = []
        for source_doi, target_doi in relationships:
            if source_doi in nodes and target_doi in nodes:
                edges.append(CitationEdge(source_doi, target_doi))
        return CitationGraph(nodes=nodes, edges=edges)

    @staticmethod
    def degree(graph: CitationGraph) -> dict[str, int]:
        degree: defaultdict[str, int] = defaultdict(int)
        for edge in graph.edges:
            degree[edge.source_doi] += 1
            degree[edge.target_doi] += 1
        return dict(degree)
