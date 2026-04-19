"""Generate self-contained HTML dependency graph visualization."""

from loom.config import LoomConfig, Language


def _get_language_color(language: Language) -> str:
    """Map language enum to hex color."""
    colors = {
        Language.PYTHON: "#3776ab",
        Language.TYPESCRIPT: "#2b7a0b",
        Language.GO: "#00add8",
        Language.RUST: "#ce422b",
    }
    return colors.get(language, "#999999")


def generate_dependency_graph(config: LoomConfig) -> str:
    """Generate a self-contained HTML dependency graph.

    Creates an SVG visualization with:
    - Nodes: repos (colored by language)
    - Edges: dependencies (with labels)
    - Badges: impact zone counts
    - Hover tooltips: zone details

    Args:
        config: LoomConfig instance

    Returns:
        Self-contained HTML string
    """
    # Build node and edge data
    nodes = []
    edges = []

    for repo in config.repos:
        color = _get_language_color(repo.language)
        nodes.append({
            "id": repo.name,
            "label": repo.name,
            "color": color,
            "language": repo.language.value,
        })

    # Count impact zones per dependency
    for dep in config.dependencies or []:
        zone_count = 0
        zone_ids = []
        for zone in config.impact_zones or []:
            if zone.source and zone.source.repo == dep.from_repo:
                if zone.target and zone.target.repo == dep.to_repo:
                    zone_count += 1
                    zone_ids.append(zone.id)

        edges.append({
            "from": dep.from_repo,
            "to": dep.to_repo,
            "label": dep.description,
            "zone_count": zone_count,
            "zone_ids": zone_ids,
        })

    # Generate SVG layout (simple horizontal hierarchy)
    svg_content = _generate_svg(nodes, edges, config)

    # Wrap in HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dependency Graph — {config.name}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f5f5;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            padding: 20px;
        }}
        h1 {{
            font-size: 24px;
            margin-bottom: 10px;
            color: #333;
        }}
        .description {{
            color: #666;
            margin-bottom: 20px;
            font-size: 14px;
        }}
        svg {{
            display: block;
            margin: 20px auto;
            border: 1px solid #eee;
            border-radius: 4px;
            background: white;
            max-width: 100%;
            height: auto;
        }}
        .legend {{
            display: flex;
            gap: 20px;
            margin-top: 20px;
            flex-wrap: wrap;
            font-size: 13px;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .legend-box {{
            width: 20px;
            height: 20px;
            border-radius: 3px;
        }}
        tooltip {{
            position: absolute;
            background: rgba(0,0,0,0.9);
            color: white;
            padding: 8px 12px;
            border-radius: 4px;
            font-size: 12px;
            pointer-events: none;
            z-index: 1000;
            max-width: 300px;
            white-space: pre-wrap;
            display: none;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Dependency Graph — {config.name}</h1>
        <div class="description">{config.description}</div>

        {svg_content}

        <div class="legend">
            <div class="legend-item">
                <div class="legend-box" style="background: #3776ab;"></div>
                <span>Python</span>
            </div>
            <div class="legend-item">
                <div class="legend-box" style="background: #2b7a0b;"></div>
                <span>TypeScript</span>
            </div>
            <div class="legend-item">
                <div class="legend-box" style="background: #00add8;"></div>
                <span>Go</span>
            </div>
            <div class="legend-item">
                <div class="legend-box" style="background: #ce422b;"></div>
                <span>Rust</span>
            </div>
        </div>
    </div>

    <script>
        // Hover tooltips
        document.querySelectorAll('[data-tooltip]').forEach(el => {{
            el.addEventListener('mouseenter', e => {{
                const tooltip = document.createElement('tooltip');
                tooltip.textContent = el.getAttribute('data-tooltip');
                tooltip.style.display = 'block';
                tooltip.style.left = e.clientX + 'px';
                tooltip.style.top = (e.clientY + 10) + 'px';
                document.body.appendChild(tooltip);
                el._tooltip = tooltip;
            }});
            el.addEventListener('mouseleave', e => {{
                if (el._tooltip) {{
                    el._tooltip.remove();
                    delete el._tooltip;
                }}
            }});
            el.addEventListener('mousemove', e => {{
                if (el._tooltip) {{
                    el._tooltip.style.left = e.clientX + 'px';
                    el._tooltip.style.top = (e.clientY + 10) + 'px';
                }}
            }});
        }});
    </script>
</body>
</html>"""

    return html


def _generate_svg(nodes: list[dict], edges: list[dict], config: LoomConfig) -> str:
    """Generate SVG content for the dependency graph.

    Args:
        nodes: List of node dicts
        edges: List of edge dicts
        config: LoomConfig for context

    Returns:
        SVG content string
    """
    if not nodes:
        return '<svg width="400" height="100"><text x="10" y="50">No repositories configured</text></svg>'

    # Simple horizontal layout: repos in a row
    node_spacing = 150
    y_pos = 100
    svg_nodes = []
    node_positions = {}

    for i, node in enumerate(nodes):
        x = 50 + i * node_spacing
        node_positions[node["id"]] = (x, y_pos)

        svg_nodes.append(f'''
    <g class="node" data-repo="{node['id']}">
        <rect x="{x - 40}" y="{y_pos - 30}" width="80" height="60"
              fill="{node['color']}" stroke="#333" stroke-width="2" rx="4"/>
        <text x="{x}" y="{y_pos + 5}" text-anchor="middle" font-size="13" font-weight="bold"
              fill="white">{node['label']}</text>
        <text x="{x}" y="{y_pos + 22}" text-anchor="middle" font-size="11" fill="white"
              opacity="0.8">{node['language']}</text>
    </g>''')

    # Generate edges
    svg_edges = []
    for edge in edges:
        if edge["from"] in node_positions and edge["to"] in node_positions:
            x1, y1 = node_positions[edge["from"]]
            x2, y2 = node_positions[edge["to"]]

            # Arrow path
            tooltip_text = f"{edge['from']} → {edge['to']}\n{edge['label']}"
            if edge["zone_count"] > 0:
                tooltip_text += f"\n\nImpact Zones: {edge['zone_count']}\n" + ", ".join(
                    edge["zone_ids"]
                )

            badge = ""
            if edge["zone_count"] > 0:
                mid_x = (x1 + x2) / 2
                mid_y = (y1 + y2) / 2 - 20
                badge = f'''
    <circle cx="{mid_x}" cy="{mid_y}" r="16" fill="#ff6b6b" stroke="#333" stroke-width="1"/>
    <text x="{mid_x}" y="{mid_y + 5}" text-anchor="middle" font-size="12" font-weight="bold"
          fill="white">{edge['zone_count']}</text>'''

            svg_edges.append(f'''
    <g class="edge" data-tooltip="{tooltip_text.replace('"', '&quot;')}">
        <line x1="{x1 + 40}" y1="{y1}" x2="{x2 - 40}" y2="{y2}"
              stroke="#999" stroke-width="2" marker-end="url(#arrowhead)"/>
        <text x="{(x1 + x2) / 2}" y="{(y1 + y2) / 2 + 15}" text-anchor="middle"
              font-size="11" fill="#666">{edge['label']}</text>
        {badge}
    </g>''')

    svg_width = max(400, 50 + len(nodes) * node_spacing + 50)
    svg_height = 280

    svg = f'''<svg width="{svg_width}" height="{svg_height}" xmlns="http://www.w3.org/2000/svg">
    <defs>
        <marker id="arrowhead" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
            <polygon points="0 0, 10 3, 0 6" fill="#999"/>
        </marker>
    </defs>
    <rect width="{svg_width}" height="{svg_height}" fill="white" stroke="#eee" stroke-width="1"/>

    {''.join(svg_edges)}
    {''.join(svg_nodes)}
</svg>'''

    return svg
