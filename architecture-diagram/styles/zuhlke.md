# Zühlke Brand Style

**Style**: Official Zühlke corporate identity — edge-to-edge gradient header band, borderless layers washed in faint brand-colour tints, purple as lead colour, 8px radius, calm and reduced
**Best for**: Zühlke proposals and RFP responses, client deliverables, internal Zühlke platforms, engineering white papers

## Style Characteristics

| Property | Value |
|---|---|
| Fill | Every layer carries a faint brand-colour tint (7–12% alpha) over white — still enforces the Zühlke 75/25 rule (primary colours ≥75%, accents ≤25%) |
| Border | 1px light gray outline only — no top/left accent borders; external layer uses a dashed tinted border (a Zühlke brand element) |
| Radius | 8px layers, 4px boxes (brand radius tokens) |
| Shadow | `0 1px 3px rgba(13,13,13,0.05)` whisper |
| Text | 95% greyscale (#0d0d0d) body, warm dark gray (#57524d) secondary — never pure black |
| Palette | Zühlke Purple (#985b9c) lead + gradient stops (violet #aa41af / blue #3c69c8 / cyan #00a5e6) + green accent |
| Typography | AA Zuehlke (Medium, no bold) titles + Lato body — official two-font system, flush left |

## Brand Rules

These rules come from the Zühlke brand guide — preserve them when adapting the template:

- **The gradient header is mandatory.** The canonical Zühlke gradient is `linear-gradient(45deg, #aa41af 5%, #3c69c8 60%, #00a5e6 100%)`, and the brand rule is that purple must dominate ~2/3 of the visible area. On a wide, short band the 45° axis compresses the purple region, so the template pushes the stops later (`22% / 78% / 100%`) to restore that dominance — keep purple clearly dominant if you change the band's proportions, and never distribute the stops evenly. The band bleeds edge-to-edge (negative margins cancel the wrapper padding); title text sits on the purple end where white passes contrast.
- **Purple is the lead, white is the canvas.** Only `.highlight` boxes and metric items carry solid purple. Layer coding lives in a faint background tint (7–12% alpha) plus the title colour — never saturated colour-washes, and no accent borders. Component boxes stay white so the tint reads as a wash, not a fill.
- **Two-font system.** Titles use AA Zuehlke (falls back to Lato, then system-ui); box content uses Lato. AA Zuehlke has no bold — display weights stop at 500 (Medium) with `letter-spacing: 0.01em`. Body/box text may use Lato 600/700.
- **Flush left.** Title band and layer titles are left-aligned, never centered or justified.
- **No pure black.** Body text is #0d0d0d (95% grey); secondary text is #57524d (warm dark gray).
- **Icons**: prefer the Zühlke plus character `+` or no icon at all in titles — avoid emojis, which break the reduced brand feel.
- Layer tints map to brand colours — every layer gets a colour, none stay grey: user = gradient blue #3c69c8, application = Zühlke Purple #985b9c, ai = gradient cyan #00a5e6, data = Zühlke Green #00cc66, infra = gradient violet #aa41af, external = Bright Blue #66ccff with a dashed border (wireframe aesthetic).

## Template

<div style="width: 1200px; box-sizing: border-box; position: relative; background: #ffffff; padding: 20px; border-radius: 8px; border: 1px solid #cccccc; font-family: 'Lato', system-ui, -apple-system, sans-serif;">
  <style scoped>
    .arch-wrapper { display: flex; gap: 12px; }.arch-sidebar { width: 165px; flex-shrink: 0; }.arch-main { flex: 1; min-width: 0; }.arch-title { margin: -20px -20px 18px -20px; padding: 16px 24px; background: linear-gradient(45deg, #aa41af 22%, #3c69c8 78%, #00a5e6 100%); border-radius: 8px 8px 0 0; text-align: left; font-family: 'AA Zuehlke', 'Lato', system-ui, sans-serif; font-size: 22px; font-weight: 500; letter-spacing: 0.01em; color: #ffffff; }
    .arch-layer { margin: 8px 0; padding: 14px; border-radius: 8px; background: #ffffff; border: 1px solid #e6e6e6; box-shadow: 0 1px 3px rgba(13, 13, 13, 0.05); }.arch-layer-title { font-family: 'AA Zuehlke', 'Lato', system-ui, sans-serif; font-size: 13px; font-weight: 500; letter-spacing: 0.01em; margin-bottom: 10px; text-align: left; }
    .arch-grid { display: grid; gap: 8px; }.arch-grid-2 { grid-template-columns: repeat(2, 1fr); }.arch-grid-3 { grid-template-columns: repeat(3, 1fr); }.arch-grid-4 { grid-template-columns: repeat(4, 1fr); }.arch-grid-5 { grid-template-columns: repeat(5, 1fr); }.arch-grid-6 { grid-template-columns: repeat(6, 1fr); }
    .arch-box { border-radius: 4px; padding: 8px; text-align: center; font-size: 11px; font-weight: 600; line-height: 1.35; color: #0d0d0d; background: #ffffff; border: 1px solid #e0e0e0; }.arch-box.highlight { background: #985b9c; border: 1px solid #985b9c; color: #ffffff; }.arch-box.tech { font-size: 10px; font-weight: 400; color: #57524d; background: #fafafa; }
    .arch-layer.external { background: rgba(102, 204, 255, 0.12); border: 1px dashed #7fbde0; }.arch-layer.external .arch-layer-title { color: #33708f; }.arch-layer.user { background: rgba(60, 105, 200, 0.07); }.arch-layer.user .arch-layer-title { color: #30549f; }.arch-layer.application { background: rgba(152, 91, 156, 0.08); }.arch-layer.application .arch-layer-title { color: #7a4a7e; }.arch-layer.ai { background: rgba(0, 165, 230, 0.07); }.arch-layer.ai .arch-layer-title { color: #007bad; }.arch-layer.data { background: rgba(0, 204, 102, 0.07); }.arch-layer.data .arch-layer-title { color: #007a3d; }.arch-layer.infra { background: rgba(170, 65, 175, 0.07); }.arch-layer.infra .arch-layer-title { color: #8a3490; }
    .arch-sidebar-panel { border-radius: 8px; padding: 10px; background: #ffffff; border: 1px solid #e6e6e6; margin-bottom: 8px; box-shadow: 0 1px 3px rgba(13, 13, 13, 0.05); }.arch-sidebar-title { font-family: 'AA Zuehlke', 'Lato', system-ui, sans-serif; font-size: 12px; font-weight: 500; letter-spacing: 0.01em; text-align: left; color: #7a4a7e; margin-bottom: 6px; }.arch-sidebar-item { font-size: 10px; text-align: center; color: #57524d; background: #fafafa; padding: 5px; border-radius: 4px; margin: 3px 0; border: 1px solid #e6e6e6; }.arch-sidebar-item.metric { background: rgba(152, 91, 156, 0.08); border: 1px solid #985b9c; color: #7a4a7e; font-weight: 700; }
  </style>
  <div class="arch-title">System Architecture</div>
  <div class="arch-wrapper">
    <div class="arch-sidebar">
      <div class="arch-sidebar-panel"><div class="arch-sidebar-title">Monitoring</div><div class="arch-sidebar-item">App Metrics</div><div class="arch-sidebar-item">Perf Tracking</div><div class="arch-sidebar-item">Health Checks</div><div class="arch-sidebar-item">Alerts</div></div>
      <div class="arch-sidebar-panel"><div class="arch-sidebar-title">Analytics</div><div class="arch-sidebar-item">User Behavior</div><div class="arch-sidebar-item">Business KPIs</div><div class="arch-sidebar-item">Tech Metrics</div><div class="arch-sidebar-item">Reports</div></div>
      <div class="arch-sidebar-panel"><div class="arch-sidebar-title">Ops</div><div class="arch-sidebar-item">CI/CD Pipeline</div><div class="arch-sidebar-item">Deployment</div><div class="arch-sidebar-item">Config</div><div class="arch-sidebar-item">Maintenance</div></div>
    </div>
    <div class="arch-main">
      <div class="arch-layer user">
        <div class="arch-layer-title">User Interface Layer</div>
        <div class="arch-grid arch-grid-4"><div class="arch-box">Web App<br><small>React/Vue</small></div><div class="arch-box">Mobile App<br><small>React Native</small></div><div class="arch-box">Desktop App<br><small>Electron</small></div><div class="arch-box">API Client<br><small>REST/GraphQL</small></div></div>
      </div>
      <div class="arch-layer application">
        <div class="arch-layer-title">Application Services</div>
        <div class="arch-grid arch-grid-3"><div class="arch-box">Business Logic<br><small>Core Services</small></div><div class="arch-box highlight">API Gateway<br><small>Routing & Auth</small></div><div class="arch-box">Background Jobs<br><small>Queue Processing</small></div></div>
      </div>
      <div class="arch-layer ai">
        <div class="arch-layer-title">Intelligence Layer</div>
        <div class="arch-grid arch-grid-2"><div class="arch-box">ML Models<br><small>Inference Engine</small></div><div class="arch-box">Rule Engine<br><small>Business Rules</small></div></div>
      </div>
      <div class="arch-layer data">
        <div class="arch-layer-title">Data Layer</div>
        <div class="arch-grid arch-grid-4"><div class="arch-box tech">Primary DB<br><small>PostgreSQL</small></div><div class="arch-box tech">Cache<br><small>Redis</small></div><div class="arch-box tech">Search<br><small>Elasticsearch</small></div><div class="arch-box tech">File Storage<br><small>S3/MinIO</small></div></div>
      </div>
      <div class="arch-layer infra">
        <div class="arch-layer-title">Infrastructure</div>
        <div class="arch-grid arch-grid-5"><div class="arch-box tech">Container<br><small>Docker/K8s</small></div><div class="arch-box tech">Load Balancer<br><small>Nginx</small></div><div class="arch-box tech">Message Queue<br><small>RabbitMQ</small></div><div class="arch-box tech">Logging<br><small>ELK Stack</small></div><div class="arch-box tech">CDN<br><small>CloudFlare</small></div></div>
      </div>
      <div class="arch-layer external">
        <div class="arch-layer-title">External Services</div>
        <div class="arch-grid arch-grid-4"><div class="arch-box tech">Third-party APIs<br><small>Payment/Auth</small></div><div class="arch-box tech">Cloud Services<br><small>AWS/Azure</small></div><div class="arch-box tech">SaaS Tools<br><small>Analytics</small></div><div class="arch-box tech">Integrations<br><small>Webhooks</small></div></div>
      </div>
    </div>
    <div class="arch-sidebar">
      <div class="arch-sidebar-panel"><div class="arch-sidebar-title">Security</div><div class="arch-sidebar-item">Authentication</div><div class="arch-sidebar-item">Authorization</div><div class="arch-sidebar-item">Encryption</div><div class="arch-sidebar-item">Network Sec</div></div>
      <div class="arch-sidebar-panel"><div class="arch-sidebar-title">Compliance</div><div class="arch-sidebar-item">Audit Logging</div><div class="arch-sidebar-item">Data Privacy</div><div class="arch-sidebar-item">Regulatory</div><div class="arch-sidebar-item">Standards</div></div>
      <div class="arch-sidebar-panel"><div class="arch-sidebar-title">Backup</div><div class="arch-sidebar-item">Data Backup</div><div class="arch-sidebar-item">Disaster Recovery</div><div class="arch-sidebar-item">HA</div><div class="arch-sidebar-item">Failover</div></div>
    </div>
  </div>
</div>
