"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import * as d3 from "d3";
import { ZoomIn, ZoomOut, Maximize2, X } from "lucide-react";
import type { GraphNode, GraphEdge } from "@/lib/types";

interface KnowledgeGraphProps {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

/** 节点子类型对应的颜色 */
const NODE_COLORS: Record<string, string> = {
  sage: "#b91c1c",       // 朱砂 - 至圣
  disciple: "#8a8050",   // 青铜 - 弟子
  lineage: "#6b4f30",    // 深褐 - 传承
  concept: "#44403c",    // 墨色 - 概念
};

interface SimNode extends GraphNode, d3.SimulationNodeDatum {}
interface SimEdge extends d3.SimulationLinkDatum<SimNode> {
  relation: string;
  label?: string;
  description?: string;
}

export default function KnowledgeGraph({ nodes, edges }: KnowledgeGraphProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const simulationRef = useRef<d3.Simulation<SimNode, SimEdge> | null>(null);
  const zoomRef = useRef<d3.ZoomBehavior<SVGSVGElement, unknown> | null>(null);
  const [selectedNode, setSelectedNode] = useState<SimNode | null>(null);
  const [relatedEdges, setRelatedEdges] = useState<SimEdge[]>([]);
  const [width, setWidth] = useState(800);
  const [height, setHeight] = useState(600);

  // 响应式调整尺寸
  useEffect(() => {
    const updateSize = () => {
      if (containerRef.current) {
        const w = containerRef.current.clientWidth;
        const h = Math.max(500, Math.min(700, w * 0.65));
        setWidth(w);
        setHeight(h);
      }
    };
    updateSize();
    window.addEventListener("resize", updateSize);
    return () => window.removeEventListener("resize", updateSize);
  }, []);

  // 绘制力导向图
  const drawGraph = useCallback(() => {
    if (!svgRef.current || nodes.length === 0) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    // 缩放容器
    const g = svg.append("g");

    // 缩放行为
    const zoom = d3
      .zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.3, 3])
      .on("zoom", (event) => {
        g.attr("transform", event.transform.toString());
      });

    svg.call(zoom);
    zoomRef.current = zoom;

    // 箭头定义
    svg
      .append("defs")
      .append("marker")
      .attr("id", "arrowhead")
      .attr("viewBox", "0 -5 10 10")
      .attr("refX", 28)
      .attr("refY", 0)
      .attr("markerWidth", 6)
      .attr("markerHeight", 6)
      .attr("orient", "auto")
      .append("path")
      .attr("d", "M0,-5L10,0L0,5")
      .attr("fill", "#a8a29e");

    // 准备数据副本
    const simNodes: SimNode[] = nodes.map((n) => ({ ...n }));
    const nodeMap = new Map(simNodes.map((n) => [n.id, n]));
    const simEdges: SimEdge[] = edges
      .filter((e) => nodeMap.has(e.source) && nodeMap.has(e.target))
      .map((e) => ({
        ...e,
        source: nodeMap.get(e.source)!,
        target: nodeMap.get(e.target)!,
      }));

    // 力模拟
    const simulation = d3
      .forceSimulation<SimNode>(simNodes)
      .force(
        "link",
        d3
          .forceLink<SimNode, SimEdge>(simEdges)
          .id((d) => d.id)
          .distance(100)
          .strength(0.6)
      )
      .force("charge", d3.forceManyBody().strength(-400))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force(
        "collision",
        d3.forceCollide<SimNode>().radius((d) => getNodeRadius(d) + 8)
      );

    simulationRef.current = simulation;

    // 绘制边
    const link = g
      .append("g")
      .attr("class", "links")
      .selectAll("line")
      .data(simEdges)
      .enter()
      .append("line")
      .attr("stroke", "#d6d3d1")
      .attr("stroke-width", 1.5)
      .attr("stroke-opacity", 0.6)
      .attr("marker-end", "url(#arrowhead)");

    // 边标签
    const linkLabel = g
      .append("g")
      .attr("class", "link-labels")
      .selectAll("text")
      .data(simEdges)
      .enter()
      .append("text")
      .attr("font-size", 9)
      .attr("fill", "#a8a29e")
      .attr("text-anchor", "middle")
      .attr("pointer-events", "none")
      .text((d) => d.label || "");

    // 绘制节点组
    const node = g
      .append("g")
      .attr("class", "nodes")
      .selectAll("g")
      .data(simNodes)
      .enter()
      .append("g")
      .attr("cursor", "pointer")
      .call(
        d3
          .drag<SVGGElement, SimNode>()
          .on("start", (event, d) => {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
          })
          .on("drag", (event, d) => {
            d.fx = event.x;
            d.fy = event.y;
          })
          .on("end", (event, d) => {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
          })
      );

    // 节点圆形
    node
      .append("circle")
      .attr("r", (d) => getNodeRadius(d))
      .attr("fill", (d) => NODE_COLORS[d.subtype || d.type] || NODE_COLORS.concept)
      .attr("stroke", "#faf6ed")
      .attr("stroke-width", 2)
      .attr("opacity", 0.9)
      .on("mouseover", function (event, d) {
        d3.select(this).attr("opacity", 1).attr("stroke-width", 3);
        // 高亮相关边
        link.attr("stroke-opacity", (l) =>
          (l.source as SimNode).id === d.id || (l.target as SimNode).id === d.id ? 1 : 0.2
        );
        link.attr("stroke", (l) =>
          (l.source as SimNode).id === d.id || (l.target as SimNode).id === d.id ? "#b91c1c" : "#d6d3d1"
        );
      })
      .on("mouseout", function () {
        d3.select(this).attr("opacity", 0.9).attr("stroke-width", 2);
        link.attr("stroke-opacity", 0.6).attr("stroke", "#d6d3d1");
      })
      .on("click", (event, d) => {
        event.stopPropagation();
        const related = simEdges.filter(
          (e) => (e.source as SimNode).id === d.id || (e.target as SimNode).id === d.id
        );
        setSelectedNode(d);
        setRelatedEdges(related);
      });

    // 节点标签
    node
      .append("text")
      .attr("dy", (d) => getNodeRadius(d) + 14)
      .attr("text-anchor", "middle")
      .attr("font-size", 12)
      .attr("font-family", '"Noto Serif SC", serif')
      .attr("fill", "#292524")
      .attr("pointer-events", "none")
      .text((d) => d.label);

    // 节点类型标识（概念节点用方形）
    node
      .filter((d) => d.type === "concept")
      .select("circle")
      .attr("rx", 0);

    // tick 更新位置
    simulation.on("tick", () => {
      link
        .attr("x1", (d) => (d.source as SimNode).x!)
        .attr("y1", (d) => (d.source as SimNode).y!)
        .attr("x2", (d) => (d.target as SimNode).x!)
        .attr("y2", (d) => (d.target as SimNode).y!);

      linkLabel
        .attr("x", (d) => ((d.source as SimNode).x! + (d.target as SimNode).x!) / 2)
        .attr("y", (d) => ((d.source as SimNode).y! + (d.target as SimNode).y!) / 2);

      node.attr("transform", (d) => `translate(${d.x},${d.y})`);
    });

    // 点击空白取消选中
    svg.on("click", () => {
      setSelectedNode(null);
      setRelatedEdges([]);
    });

    return () => {
      simulation.stop();
    };
  }, [nodes, edges, width, height]);

  useEffect(() => {
    drawGraph();
    return () => {
      if (simulationRef.current) {
        simulationRef.current.stop();
      }
    };
  }, [drawGraph]);

  /** 获取节点半径 */
  const getNodeRadius = (node: GraphNode): number => {
    if (node.subtype === "sage") return 28;
    if (node.subtype === "disciple") return 20;
    if (node.subtype === "lineage") return 22;
    return 16;
  };

  /** 缩放控制 */
  const handleZoom = (factor: number) => {
    if (!svgRef.current || !zoomRef.current) return;
    d3.select(svgRef.current)
      .transition()
      .duration(200)
      .call(zoomRef.current.scaleBy, factor);
  };

  /** 重置视图 */
  const handleReset = () => {
    if (!svgRef.current || !zoomRef.current) return;
    d3.select(svgRef.current)
      .transition()
      .duration(300)
      .call(zoomRef.current.transform, d3.zoomIdentity);
  };

  return (
    <div ref={containerRef} className="relative w-full">
      {/* 工具栏 */}
      <div className="absolute right-3 top-3 z-10 flex flex-col gap-1.5">
        <button
          onClick={() => handleZoom(1.3)}
          className="flex h-9 w-9 items-center justify-center rounded-lg bg-white/80 text-ink-600 shadow-scroll backdrop-blur transition-colors hover:bg-white hover:text-ink-800"
          title="放大"
        >
          <ZoomIn size={16} />
        </button>
        <button
          onClick={() => handleZoom(0.7)}
          className="flex h-9 w-9 items-center justify-center rounded-lg bg-white/80 text-ink-600 shadow-scroll backdrop-blur transition-colors hover:bg-white hover:text-ink-800"
          title="缩小"
        >
          <ZoomOut size={16} />
        </button>
        <button
          onClick={handleReset}
          className="flex h-9 w-9 items-center justify-center rounded-lg bg-white/80 text-ink-600 shadow-scroll backdrop-blur transition-colors hover:bg-white hover:text-ink-800"
          title="重置"
        >
          <Maximize2 size={16} />
        </button>
      </div>

      {/* 图例 */}
      <div className="absolute left-3 top-3 z-10 flex flex-col gap-1.5 rounded-lg bg-white/80 px-3 py-2 text-xs shadow-scroll backdrop-blur">
        <div className="flex items-center gap-2">
          <span className="h-3 w-3 rounded-full" style={{ background: NODE_COLORS.sage }} />
          <span className="text-ink-600">至圣</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="h-3 w-3 rounded-full" style={{ background: NODE_COLORS.disciple }} />
          <span className="text-ink-600">弟子</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="h-3 w-3 rounded-full" style={{ background: NODE_COLORS.lineage }} />
          <span className="text-ink-600">传承</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="h-3 w-3 rounded-full" style={{ background: NODE_COLORS.concept }} />
          <span className="text-ink-600">概念</span>
        </div>
      </div>

      {/* SVG 画布 */}
      <svg
        ref={svgRef}
        width={width}
        height={height}
        className="rounded-lg border border-ink-100 bg-rice-50/50"
        style={{ touchAction: "none" }}
      />

      {/* 节点详情面板 */}
      {selectedNode && (
        <div className="absolute bottom-3 left-3 right-3 z-20 max-h-[45%] overflow-y-auto rounded-lg bg-white/95 p-4 shadow-popup backdrop-blur md:right-auto md:max-w-md">
          <div className="mb-2 flex items-start justify-between">
            <div>
              <h3 className="font-serif text-lg font-semibold text-ink-800">
                {selectedNode.label}
              </h3>
              {selectedNode.courtesy_name && (
                <p className="text-xs text-ink-400">
                  字 {selectedNode.courtesy_name}
                  {selectedNode.real_name && ` · 本名 ${selectedNode.real_name}`}
                </p>
              )}
            </div>
            <button
              onClick={() => setSelectedNode(null)}
              className="text-ink-400 hover:text-ink-600"
            >
              <X size={18} />
            </button>
          </div>

          {selectedNode.era && (
            <p className="mb-1 text-xs text-bronze-500">
              {selectedNode.era}
              {selectedNode.birth_year !== undefined && (
                <span className="ml-2">
                  （{selectedNode.birth_year < 0 ? `前${-selectedNode.birth_year}` : selectedNode.birth_year}
                  {" — "}
                  {selectedNode.death_year! < 0 ? `前${-selectedNode.death_year!}` : selectedNode.death_year}）
                </span>
              )}
            </p>
          )}

          {selectedNode.description && (
            <p className="mb-2 text-sm leading-relaxed text-ink-600">
              {selectedNode.description}
            </p>
          )}

          {selectedNode.core_thought && (
            <div className="mb-2">
              <span className="text-xs font-medium text-cinnabar-600">核心思想：</span>
              <span className="text-sm text-ink-600">{selectedNode.core_thought}</span>
            </div>
          )}

          {selectedNode.tags && selectedNode.tags.length > 0 && (
            <div className="mb-2 flex flex-wrap gap-1">
              {selectedNode.tags.map((tag) => (
                <span
                  key={tag}
                  className="rounded bg-rice-200 px-2 py-0.5 text-xs text-ink-500"
                >
                  {tag}
                </span>
              ))}
            </div>
          )}

          {relatedEdges.length > 0 && (
            <div className="mt-2 border-t border-ink-100 pt-2">
              <p className="mb-1 text-xs font-medium text-ink-400">关联关系</p>
              <div className="space-y-1">
                {relatedEdges.map((edge, i) => {
                  const src = edge.source as SimNode;
                  const tgt = edge.target as SimNode;
                  const otherNode =
                    src.id === selectedNode.id ? tgt : src;
                  const direction =
                    src.id === selectedNode.id ? "→" : "←";
                  return (
                    <div key={i} className="text-xs text-ink-500">
                      <span className="text-cinnabar-500">{direction}</span>
                      <span className="mx-1 font-medium">{otherNode.label}</span>
                      <span className="text-ink-300">（{edge.relation}）</span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
