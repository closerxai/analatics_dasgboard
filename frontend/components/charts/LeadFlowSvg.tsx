'use client';

// Embedded static SVG flow — mirrors the emp_ui Lead Lifecycle Flow exactly.
// Counts come from props so they can be driven by real data in future.
interface Props {
  onClick?: (nodeId: string, count: number) => void;
}

export default function LeadFlowSvg({ onClick }: Props) {
  const N: Record<string, { x: number; y: number; w: number; h: number; label: string; kind: string; n?: number; sub?: string }> = {
    s_outdoor:   { x: 20, y: 40, w:130, h:34, label:'Outdoor', kind:'src' },
    s_print:     { x: 20, y: 80, w:130, h:34, label:'Print', kind:'src' },
    s_radio:     { x: 20, y:120, w:130, h:34, label:'Radio', kind:'src' },
    s_website1:  { x: 20, y:160, w:130, h:34, label:'Website', kind:'src' },
    s_digital:   { x: 20, y:200, w:130, h:34, label:'Digital Portal', kind:'src' },
    s_pportal:   { x: 20, y:240, w:130, h:34, label:'Property Portal', kind:'src' },
    s_google:    { x: 20, y:430, w:130, h:34, label:'Google Leads', kind:'src' },
    s_igdm:      { x: 20, y:470, w:130, h:34, label:'IG DM', kind:'src' },
    s_fbdm:      { x: 20, y:510, w:130, h:34, label:'FB DM', kind:'src' },
    s_meta:      { x: 20, y:550, w:130, h:34, label:'Meta Leads', kind:'src' },
    s_website2:  { x: 20, y:590, w:130, h:34, label:'Website', kind:'src' },
    s_yt:        { x: 20, y:630, w:130, h:34, label:'YouTube / DM', kind:'src' },
    inbound:     { x:220, y:170, w:160, h:42, label:'Inbound Calling', kind:'neu', n:612 },
    outbound:    { x:220, y:470, w:160, h:42, label:'Outbound Calling', kind:'neu', n:672 },
    answered:    { x:420, y:430, w:130, h:34, label:'Answered', kind:'ops', n:419 },
    not_ans_1:   { x:420, y:500, w:200, h:58, label:'Not Answered', sub:'2×/day · alt days / 6 days', kind:'neg', n:193 },
    not_ans_2:   { x:420, y:590, w:200, h:42, label:'Not Answered', sub:'Call again after 7 days', kind:'neg', n:60 },
    ai_agent:    { x:420, y:170, w:180, h:50, label:'AI sales agent', sub:'Lead source confirm', kind:'neu', n:612 },
    wa_brochure: { x:640, y:130, w:140, h:56, label:'Brochure sent to all use cases', kind:'wa' },
    wa_confirm:  { x:640, y:230, w:140, h:64, label:'WhatsApp confirmation with call-back schedule', kind:'wa' },
    manual:      { x:880, y:40,  w:140, h:42, label:'Manually update the status', kind:'wa' },
    direct_call: { x:830, y:170, w:170, h:36, label:'Direct call to sales', kind:'neu', n:58 },
    cbs:         { x:830, y:220, w:170, h:36, label:'Call Back Schedule', kind:'ops', n:321 },
    site_book:   { x:830, y:270, w:170, h:36, label:'Site Visit Book', kind:'pos', n:518 },
    future_lead: { x:830, y:410, w:170, h:36, label:'Future Lead', kind:'neu', n:142 },
    disqualified:{ x:830, y:480, w:170, h:36, label:'Disqualified', kind:'neg', n:96 },
    sales_rep:   { x:830, y:360, w:170, h:36, label:'Sales rep', kind:'ops', n:198 },
    get_details: { x:1060, y:410, w:200, h:46, label:'Get details', sub:'Location, Budget & unit type', kind:'neu' },
    wa_visit:    { x:1060, y:220, w:140, h:56, label:'WhatsApp Visit confirmations to sales & lead', kind:'wa' },
    wa_reminder: { x:1060, y:310, w:140, h:56, label:'WhatsApp Visit reminder (2 hours) to sales & lead', kind:'wa' },
    reschedule:  { x:1240, y:170, w:170, h:36, label:'Site Visit Reschedule', kind:'info', n:84 },
    canceled:    { x:1240, y:220, w:170, h:36, label:'Canceled', kind:'neg', n:62 },
    feedback:    { x:1240, y:270, w:170, h:42, label:'Feedback', sub:'Reason for cancel?', kind:'dark' },
    site_done:   { x:1240, y:360, w:170, h:36, label:'Site Visit Done', kind:'pos', n:318 },
    mygate:      { x:1460, y:360, w:150, h:46, label:'Mygate integration', kind:'wa' },
    booking:     { x:1460, y:430, w:150, h:36, label:'Booking', kind:'pos', n:47 },
    not_int:     { x:1460, y:480, w:150, h:36, label:'Not Interested', kind:'neg', n:189 },
    revisit:     { x:1460, y:540, w:150, h:36, label:'Revisit Schedule', kind:'info', n:54 },
    followup:    { x:1460, y:600, w:150, h:46, label:'Follow-up – Human calling', sub:'Status update by sales', kind:'info', n:29 },
  };

  const STYLES: Record<string, { fill: string; stroke: string; fg: string }> = {
    src:  { fill:'var(--panel)',         stroke:'var(--line-2)',              fg:'var(--ink)' },
    neu:  { fill:'var(--panel)',         stroke:'var(--line-2)',              fg:'var(--ink)' },
    pos:  { fill:'oklch(62% 0.14 150)', stroke:'oklch(55% 0.14 150)',        fg:'white' },
    neg:  { fill:'oklch(62% 0.16 25)',  stroke:'oklch(55% 0.16 25)',         fg:'white' },
    ops:  { fill:'oklch(72% 0.14 65)',  stroke:'oklch(65% 0.14 65)',         fg:'white' },
    info: { fill:'oklch(74% 0.08 195)', stroke:'oklch(62% 0.09 195)',        fg:'oklch(20% 0.03 195)' },
    dark: { fill:'oklch(42% 0.01 250)', stroke:'oklch(30% 0.01 250)',        fg:'white' },
    wa:   { fill:'oklch(94% 0.08 85)',  stroke:'oklch(78% 0.12 85)',         fg:'oklch(35% 0.08 75)' },
  };

  type EdgeTuple = [string, string, string, string, string, number?, string?];
  const E: EdgeTuple[] = [
    ['s_outdoor','r','inbound','l','neu',190],['s_print','r','inbound','l','neu',190],
    ['s_radio','r','inbound','l','neu',190],['s_website1','r','inbound','l','neu',190],
    ['s_digital','r','inbound','l','neu',190],['s_pportal','r','inbound','l','neu',190],
    ['s_google','r','outbound','l','neu',190],['s_igdm','r','outbound','l','neu',190],
    ['s_fbdm','r','outbound','l','neu',190],['s_meta','r','outbound','l','neu',190],
    ['s_website2','r','outbound','l','neu',190],['s_yt','r','outbound','l','neu',190],
    ['inbound','r','ai_agent','l','neu'],['ai_agent','r','wa_brochure','l','alt'],
    ['ai_agent','r','wa_confirm','l','alt'],['wa_brochure','r','direct_call','l','neu',810],
    ['wa_confirm','r','cbs','l','neu',810],['wa_confirm','r','site_book','l','neu',810],
    ['outbound','r','answered','l','neu'],['outbound','r','not_ans_1','l','neg'],
    ['not_ans_1','b','not_ans_2','t','neg'],['answered','r','sales_rep','l','neu',800],
    ['answered','r','cbs','l','neu',800],['answered','r','site_book','l','neu',800],
    ['answered','r','future_lead','l','neu',800],['answered','r','disqualified','l','neg',800],
    ['ai_agent','r','future_lead','l','neu',810],['ai_agent','r','disqualified','l','neg',810],
    ['manual','b','direct_call','t','alt'],['future_lead','r','get_details','l','neu'],
    ['disqualified','r','get_details','l','neg'],['cbs','r','wa_visit','l','alt'],
    ['site_book','r','wa_visit','l','alt'],['wa_visit','r','reschedule','l','pos'],
    ['wa_visit','r','canceled','l','neg'],['wa_visit','r','site_done','l','pos'],
    ['wa_reminder','r','site_done','l','alt'],['site_book','r','wa_reminder','l','alt',1040],
    ['reschedule','b','canceled','t','neu'],['canceled','b','feedback','t','neg'],
    ['feedback','b','site_done','t','neg'],['site_done','r','mygate','l','pos'],
    ['mygate','b','booking','t','pos'],['mygate','b','not_int','t','neg'],
    ['mygate','b','revisit','t','neu'],['revisit','b','followup','t','neu'],
    ['followup','r','revisit','r','alt',1625],
  ];

  const rx = (n: typeof N[string], s: string) => s === 'r' ? n.x + n.w : s === 'l' ? n.x : n.x + n.w / 2;
  const ry = (n: typeof N[string], s: string) => s === 't' ? n.y : s === 'b' ? n.y + n.h : n.y + n.h / 2;

  const edgeColor = (t: string) =>
    t === 'pos' ? 'oklch(62% 0.14 150)' :
    t === 'neg' ? 'oklch(62% 0.16 25)' :
    t === 'alt' ? 'oklch(72% 0.14 75)' :
    'oklch(55% 0.02 250)';

  const arrowPts = (bx: number, by: number, sb: string, color: string) => {
    const s = 5;
    const pts =
      sb === 'l' ? `${bx-s},${by-s} ${bx},${by} ${bx-s},${by+s}` :
      sb === 'r' ? `${bx+s},${by-s} ${bx},${by} ${bx+s},${by+s}` :
      sb === 't' ? `${bx-s},${by-s} ${bx},${by} ${bx+s},${by-s}` :
                   `${bx-s},${by+s} ${bx},${by} ${bx+s},${by+s}`;
    return <polygon key={`ar-${bx}-${by}`} points={pts} fill={color} stroke="none" />;
  };

  const edges = E.map(([a, sa, b, sb, type, bend], i) => {
    const na = N[a], nb = N[b];
    if (!na || !nb) return null;
    const ax = rx(na, sa), ay = ry(na, sa);
    const bx = rx(nb, sb), by = ry(nb, sb);
    let d: string;
    const mx = bend ?? (ax + bx) / 2;
    if ((sa === 'r' || sa === 'l') && (sb === 'l' || sb === 'r')) {
      d = `M ${ax} ${ay} L ${mx} ${ay} L ${mx} ${by} L ${bx} ${by}`;
    } else if ((sa === 'b' || sa === 't') && (sb === 't' || sb === 'b')) {
      const my = (ay + by) / 2;
      d = `M ${ax} ${ay} L ${ax} ${my} L ${bx} ${my} L ${bx} ${by}`;
    } else if ((sa === 'r' || sa === 'l') && (sb === 't' || sb === 'b')) {
      d = `M ${ax} ${ay} L ${mx} ${ay} L ${mx} ${by} L ${bx} ${by}`;
    } else {
      const my = (ay + by) / 2;
      d = `M ${ax} ${ay} L ${ax} ${my} L ${bx} ${my} L ${bx} ${by}`;
    }
    const color = edgeColor(type);
    const dash = type === 'alt' ? '4 3' : undefined;
    return (
      <g key={i}>
        <path d={d} fill="none" stroke={color} strokeWidth="1.4" strokeDasharray={dash} />
        {arrowPts(bx, by, sb, color)}
      </g>
    );
  });

  const nodes = Object.entries(N).map(([id, n]) => {
    const s = STYLES[n.kind] || STYLES.neu;
    const lines = n.label.split(' ').reduce<string[]>((acc, word) => {
      if (acc.length && (acc[acc.length-1] + ' ' + word).length <= 22) {
        acc[acc.length-1] += ' ' + word;
      } else acc.push(word);
      return acc;
    }, []);
    const startY = n.y + n.h / 2 + 4 - (lines.length - 1) * 6 - (n.sub ? 5 : 0);
    const subLines = n.sub ? n.sub.split(/<br\s*\/?>/i) : [];

    return (
      <g
        key={id}
        style={{ cursor: onClick ? 'pointer' : 'default' }}
        onClick={() => onClick?.(id, n.n ?? 0)}
      >
        <rect x={n.x} y={n.y} width={n.w} height={n.h} rx={6} ry={6} fill={s.fill} stroke={s.stroke} />
        <text
          x={n.x + n.w / 2} y={startY}
          textAnchor="middle" fill={s.fg}
          fontSize={n.kind === 'src' ? 11.5 : 12}
          fontWeight={n.kind === 'wa' ? 500 : 550}
          fontFamily="Inter,sans-serif"
        >
          {lines.map((ln, i) => <tspan key={i} x={n.x + n.w / 2} dy={i === 0 ? 0 : 12}>{ln}</tspan>)}
        </text>
        {subLines.map((ln, i) => (
          <text key={i} x={n.x + n.w / 2} y={n.y + n.h / 2 + 8 + i * 11 + (lines.length - 1) * 12}
            textAnchor="middle" fill={s.fg} fontSize={9.5} opacity={0.82} fontFamily="Inter,sans-serif">
            {ln.trim()}
          </text>
        ))}
        {n.n != null && (
          <text className="count" x={n.x + n.w - 8} y={n.y + 13}
            textAnchor="end" fill={s.fg} opacity={0.85}
            fontSize={11} fontFamily="JetBrains Mono,monospace" fontWeight={600}>
            {n.n}
          </text>
        )}
        <title>{n.label}{n.n != null ? ` · ${n.n} leads` : ''}</title>
      </g>
    );
  });

  return (
    <svg
      viewBox="0 0 1640 700"
      preserveAspectRatio="xMidYMid meet"
      style={{ height: 680, minWidth: 1640, display: 'block' }}
    >
      {/* Section tags */}
      {[
        [85,28,'Offline sources'],[85,418,'Online sources'],[300,28,'Intake'],
        [510,28,'Routing / AI'],[915,28,'Disposition'],[1160,28,'Qualify / Visit'],
        [1325,28,'Visit outcomes'],[1535,28,'Final stage'],
      ].map(([x,y,label]) => (
        <text key={String(label)} x={Number(x)} y={Number(y)}
          fontSize={9.5} fill="var(--ink-3)"
          style={{ textTransform:'uppercase', letterSpacing:'0.08em' }}
          fontFamily="Inter,sans-serif" fontWeight={500}>
          {label}
        </text>
      ))}
      {edges}
      {nodes}
    </svg>
  );
}
