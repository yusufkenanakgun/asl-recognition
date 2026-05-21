/* global React */
// Screens for "ASL Recognition Demo" — Android Material 3 mockups.
// Light theme only. Teal accent. Academic, minimal.

const T = {
  // surfaces
  bg: '#FFFFFF',
  surface: '#F7F8F8',
  cardBorder: '#ECEEF0',
  divider: '#EEF0F2',
  // text
  text: '#101418',
  textSec: '#5A6066',
  textTer: '#B8BDC2',
  // accent (teal)
  teal: '#00897B',
  tealDark: '#00695C',
  tealContainer: '#B2DFDB',
  tealSoft: '#E0F2F1',
  tealTint: '#F2F9F8',
  onTeal: '#FFFFFF',
};

const ROBOTO = 'Roboto, "Inter", system-ui, -apple-system, sans-serif';
const MONO = '"Roboto Mono", ui-monospace, "SF Mono", Menlo, monospace';

// ─────────────────────────────────────────────────────────────
// Material Symbols Rounded — inline SVG glyphs
// 24×24 viewBox, fill=currentColor, rounded outline style
// ─────────────────────────────────────────────────────────────
const Icon = ({ d, size = 24, color = 'currentColor', stroke = 1.8, fill = false, style }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" style={{ flexShrink: 0, ...style }}
    fill={fill ? color : 'none'} stroke={fill ? 'none' : color}
    strokeWidth={stroke} strokeLinecap="round" strokeLinejoin="round">
    {d}
  </svg>
);

const Icons = {
  home: <Icon d={<><path d="M3 11l9-8 9 8" /><path d="M5 10v10h4v-6h6v6h4V10" /></>} />,
  homeFill: <Icon fill d={<path d="M12 3.2L3 11h2v9h5v-6h4v6h5v-9h2L12 3.2z" />} />,
  abc: <Icon d={<><path d="M3 16V9a3 3 0 016 0v7" /><path d="M3 13h6" /><path d="M11 16V9a3 3 0 016 0v7" /><path d="M11 13h6" /><path d="M22 9v7" /><path d="M22 11a2 2 0 100 4 2 2 0 000-4z" /></>} />,
  abcFill: <Icon d={<><path d="M3 16V9a3 3 0 016 0v7" /><path d="M3 13h6" /><path d="M11 16V9a3 3 0 016 0v7" /><path d="M11 13h6" /><path d="M22 9v7" /><path d="M22 11a2 2 0 100 4 2 2 0 000-4z" /></>} stroke={2.4} />,
  bubble: <Icon d={<><path d="M21 12a8 8 0 01-11.5 7.2L4 21l1.8-5.5A8 8 0 1121 12z" /></>} />,
  bubbleFill: <Icon fill d={<path d="M12 3a9 9 0 00-8 13.3L2.5 21.5l5.2-1.5A9 9 0 1012 3zm-4 10a1 1 0 110-2 1 1 0 010 2zm4 0a1 1 0 110-2 1 1 0 010 2zm4 0a1 1 0 110-2 1 1 0 010 2z" />} />,
  hand: <Icon d={<><path d="M7 11V6.5a1.5 1.5 0 113 0V11" /><path d="M10 11V5a1.5 1.5 0 113 0v6" /><path d="M13 11V6a1.5 1.5 0 113 0v7" /><path d="M16 13v-2a1.5 1.5 0 113 0v5a5 5 0 01-5 5H11a4 4 0 01-3.5-2L4 17l1-1.5a2 2 0 012.8-.5L9 16" /></>} />,
  chevronDown: <Icon d={<path d="M6 9l6 6 6-6" />} />,
  chevronUp: <Icon d={<path d="M6 15l6-6 6 6" />} />,
  github: <Icon stroke={1.6} d={<path d="M12 2a10 10 0 00-3.16 19.49c.5.09.68-.22.68-.48v-1.7c-2.78.6-3.37-1.34-3.37-1.34-.46-1.16-1.12-1.47-1.12-1.47-.91-.62.07-.6.07-.6 1 .07 1.53 1.04 1.53 1.04.9 1.53 2.36 1.09 2.94.83.09-.65.35-1.1.63-1.35-2.22-.25-4.56-1.11-4.56-4.95 0-1.1.39-2 1.03-2.7-.1-.26-.45-1.28.1-2.66 0 0 .84-.27 2.75 1.03A9.55 9.55 0 0112 6.8c.85 0 1.7.11 2.5.33 1.91-1.3 2.75-1.03 2.75-1.03.55 1.38.2 2.4.1 2.66.64.7 1.03 1.6 1.03 2.7 0 3.85-2.34 4.69-4.57 4.94.36.31.68.92.68 1.86v2.76c0 .27.18.58.69.48A10 10 0 0012 2z" />} fill />,
  link: <Icon stroke={1.8} d={<><path d="M10 13a5 5 0 007 0l3-3a5 5 0 00-7-7l-1 1" /><path d="M14 11a5 5 0 00-7 0l-3 3a5 5 0 007 7l1-1" /></>} />,
  cameraOff: <Icon stroke={1.6} d={<><path d="M3 3l18 18" /><path d="M21 8v9a2 2 0 01-2 2H7" /><path d="M3 7v10a2 2 0 002 2h2" /><path d="M9 5h6l1.5 2H21" /><circle cx="12" cy="13" r="3" /></>} />,
  camera: <Icon stroke={1.6} d={<><path d="M23 19V8a2 2 0 00-2-2h-3l-2-3H8L6 6H3a2 2 0 00-2 2v11a2 2 0 002 2h18a2 2 0 002-2z" /><circle cx="12" cy="13" r="4" /></>} />,
  bolt: <Icon fill d={<path d="M13 2L4 14h6l-1 8 9-12h-6l1-8z" />} />,
  hourglass: <Icon stroke={1.8} d={<><path d="M6 2h12" /><path d="M6 22h12" /><path d="M6 2c0 5 6 6 6 10s-6 5-6 10" /><path d="M18 2c0 5-6 6-6 10s6 5 6 10" /></>} />,
  arrowRight: <Icon stroke={2} d={<path d="M5 12h14M13 6l6 6-6 6" />} />,
};

// ─────────────────────────────────────────────────────────────
// Phone frame — custom, not using android-frame's AppBar
// 412 × 892, 9:19.5 ratio close enough
// ─────────────────────────────────────────────────────────────
function Phone({ children, scroll = true }) {
  return (
    <div style={{
      width: 412, height: 892, borderRadius: 44, overflow: 'hidden',
      background: T.bg,
      border: '10px solid #1A1D20',
      boxShadow: '0 40px 80px -20px rgba(16,20,24,0.25), 0 0 0 1px rgba(16,20,24,0.04)',
      display: 'flex', flexDirection: 'column', boxSizing: 'border-box',
      fontFamily: ROBOTO,
      position: 'relative',
    }}>
      <StatusBar />
      <div style={{ flex: 1, overflow: scroll ? 'auto' : 'hidden', position: 'relative', background: T.bg }}>
        {children}
      </div>
      <NavGesture />
    </div>
  );
}

function StatusBar({ tone = 'dark' }) {
  const c = tone === 'dark' ? T.text : '#FFFFFF';
  return (
    <div style={{
      height: 36, display: 'flex', alignItems: 'center',
      justifyContent: 'space-between', padding: '0 22px 0 24px',
      position: 'relative', flexShrink: 0,
      background: 'transparent',
    }}>
      <span style={{ fontSize: 14, fontWeight: 500, color: c, letterSpacing: 0.2 }}>9:41</span>
      <div style={{
        position: 'absolute', left: '50%', top: 10, transform: 'translateX(-50%)',
        width: 22, height: 22, borderRadius: 100, background: '#0A0C0E',
      }} />
      <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
        {/* signal */}
        <svg width="16" height="11" viewBox="0 0 16 11" fill={c}><rect x="0" y="7" width="3" height="4" rx="0.5"/><rect x="4.5" y="5" width="3" height="6" rx="0.5"/><rect x="9" y="2.5" width="3" height="8.5" rx="0.5"/><rect x="13.5" y="0" width="2.5" height="11" rx="0.5"/></svg>
        {/* wifi */}
        <svg width="15" height="11" viewBox="0 0 15 11" fill={c}><path d="M7.5 2.2A11 11 0 000 5.1l1.3 1.3a9 9 0 0112.4 0L15 5.1A11 11 0 007.5 2.2z"/><path d="M7.5 5.4a7 7 0 00-4.6 1.8L4.2 8.5a5 5 0 016.6 0l1.3-1.3A7 7 0 007.5 5.4z"/><path d="M7.5 8.5a3 3 0 00-2 .8l2 2 2-2a3 3 0 00-2-.8z"/></svg>
        {/* battery */}
        <svg width="26" height="11" viewBox="0 0 26 11">
          <rect x="0.5" y="0.5" width="22" height="10" rx="2.5" fill="none" stroke={c} strokeOpacity="0.5"/>
          <rect x="2" y="2" width="14" height="7" rx="1.2" fill={c}/>
          <rect x="23" y="3.5" width="2" height="4" rx="1" fill={c} opacity="0.4"/>
        </svg>
      </div>
    </div>
  );
}

function NavGesture({ tone = 'dark' }) {
  return (
    <div style={{ height: 22, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, background: T.bg }}>
      <div style={{ width: 130, height: 4, borderRadius: 2, background: tone === 'dark' ? T.text : '#FFFFFF', opacity: 0.85 }} />
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// Top app bar (Material 3 small, left-aligned)
// ─────────────────────────────────────────────────────────────
function AppBar({ title, trailing }) {
  return (
    <div style={{
      height: 56, display: 'flex', alignItems: 'center', padding: '0 16px',
      background: T.bg, flexShrink: 0,
    }}>
      <div style={{ flex: 1, fontSize: 20, fontWeight: 500, color: T.text, letterSpacing: 0 }}>{title}</div>
      {trailing}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// Bottom navigation bar — 3 tabs
// ─────────────────────────────────────────────────────────────
function BottomNav({ active = 'home' }) {
  const tabs = [
    { id: 'home', label: 'Home', icon: Icons.home, iconFill: Icons.homeFill },
    { id: 'letters', label: 'Letters', icon: Icons.abc, iconFill: Icons.abcFill },
    { id: 'words', label: 'Words', icon: Icons.bubble, iconFill: Icons.bubbleFill },
  ];
  return (
    <div style={{
      display: 'flex', background: T.bg,
      borderTop: `1px solid ${T.divider}`,
      paddingTop: 12, paddingBottom: 12,
      flexShrink: 0,
    }}>
      {tabs.map(t => {
        const isActive = t.id === active;
        return (
          <div key={t.id} style={{
            flex: 1, display: 'flex', flexDirection: 'column',
            alignItems: 'center', gap: 4,
          }}>
            <div style={{
              width: 64, height: 32, borderRadius: 16,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              background: isActive ? T.tealContainer : 'transparent',
              color: isActive ? T.tealDark : T.textSec,
            }}>
              {React.cloneElement(isActive ? t.iconFill : t.icon, { size: 22 })}
            </div>
            <span style={{
              fontSize: 12, fontWeight: isActive ? 500 : 400,
              color: isActive ? T.text : T.textSec, letterSpacing: 0.3,
            }}>{t.label}</span>
          </div>
        );
      })}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// SCREEN 1 — Home
// ─────────────────────────────────────────────────────────────
function HomeScreen() {
  return (
    <Phone>
      <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
        <AppBar title="ASL Recognition Demo" />

        <div style={{ flex: 1, overflow: 'auto', padding: '4px 20px 24px' }}>
          {/* Header */}
          <div style={{ padding: '12px 0 24px' }}>
            <h1 style={{
              fontSize: 26, fontWeight: 500, color: T.text,
              lineHeight: 1.2, margin: '0 0 12px', letterSpacing: -0.3,
              textWrap: 'pretty',
            }}>Real-time American Sign Language Recognition</h1>
            <p style={{
              fontSize: 14, color: T.textSec, lineHeight: 1.55, margin: 0,
              textWrap: 'pretty',
            }}>On-device inference for static letters and dynamic word-level signs, compared across image-based and landmark-based approaches.</p>
          </div>

          {/* Two action cards */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginBottom: 24 }}>
            <ActionCard
              primary
              icon={Icons.hand}
              title="Recognize Letters"
              caption="A–Z, del, nothing, space (29 classes)"
            />
            <ActionCard
              icon={Icons.bubbleFill}
              title="Recognize Words"
              caption="100 ASL word-level signs (WLASL-100)"
            />
          </div>

          {/* About section (expanded) */}
          <AboutSection />

          {/* Models table */}
          <ModelsTable />

          {/* Dataset caption */}
          <div style={{
            fontSize: 11, color: T.textTer, marginTop: 16,
            textAlign: 'center', letterSpacing: 0.2,
          }}>Datasets · ASL Alphabet · WLASL-100</div>
        </div>

        <BottomNav active="home" />
      </div>
    </Phone>
  );
}

function ActionCard({ icon, title, caption, primary }) {
  return (
    <div style={{
      padding: '20px 20px 22px',
      borderRadius: 16,
      background: primary ? T.teal : T.bg,
      border: primary ? 'none' : `1px solid ${T.cardBorder}`,
      boxShadow: primary ? '0 1px 2px rgba(0,137,123,0.20), 0 4px 12px -4px rgba(0,137,123,0.18)' : '0 1px 0 rgba(16,20,24,0.03)',
      display: 'flex', alignItems: 'center', gap: 18,
    }}>
      <div style={{
        width: 52, height: 52, borderRadius: 14,
        background: primary ? 'rgba(255,255,255,0.18)' : T.tealSoft,
        color: primary ? '#fff' : T.teal,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        flexShrink: 0,
      }}>
        {React.cloneElement(icon, { size: 28, stroke: 1.8 })}
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{
          fontSize: 17, fontWeight: 500, lineHeight: 1.2,
          color: primary ? '#fff' : T.text, marginBottom: 4,
        }}>{title}</div>
        <div style={{
          fontSize: 13, color: primary ? 'rgba(255,255,255,0.85)' : T.textSec,
          lineHeight: 1.4,
        }}>{caption}</div>
      </div>
      <div style={{ color: primary ? 'rgba(255,255,255,0.9)' : T.textTer }}>
        {React.cloneElement(Icons.arrowRight, { size: 20 })}
      </div>
    </div>
  );
}

function AboutSection() {
  return (
    <div style={{
      border: `1px solid ${T.cardBorder}`, borderRadius: 16,
      background: T.bg, overflow: 'hidden',
    }}>
      {/* Header (expanded) */}
      <div style={{
        display: 'flex', alignItems: 'center', padding: '14px 18px',
        borderBottom: `1px solid ${T.divider}`,
      }}>
        <div style={{ flex: 1, fontSize: 14, fontWeight: 500, color: T.text }}>About this project</div>
        <div style={{ color: T.textSec }}>{React.cloneElement(Icons.chevronUp, { size: 20, stroke: 2 })}</div>
      </div>

      <div style={{ padding: '14px 18px 18px' }}>
        <InfoRow label="Project" value="CSE492 Engineering Project" small />
        <div style={{
          fontSize: 12, color: T.textSec, lineHeight: 1.5,
          margin: '2px 0 12px', textWrap: 'pretty',
        }}>AI-Powered Sign Language Recognition System: A Comparative Study of Image-Based and Landmark-Based Approaches</div>
        <InfoRow label="Author" value="Yusuf Kenan Akgün" />
        <InfoRow label="Institution" value="Yeditepe University" />
        <InfoRow label="Year" value="2026" />

        <div style={{
          display: 'flex', alignItems: 'center', gap: 8,
          marginTop: 14, paddingTop: 14, borderTop: `1px solid ${T.divider}`,
          color: T.teal, fontSize: 13, fontWeight: 500,
        }}>
          {React.cloneElement(Icons.github, { size: 18, color: T.teal })}
          <span>github.com/ykakgun/asl-recognition</span>
          <div style={{ flex: 1 }} />
          {React.cloneElement(Icons.link, { size: 16, color: T.teal })}
        </div>
      </div>
    </div>
  );
}

function InfoRow({ label, value, small }) {
  return (
    <div style={{ display: 'flex', alignItems: 'baseline', gap: 10, padding: small ? '2px 0' : '4px 0' }}>
      <div style={{ fontSize: 11, color: T.textTer, letterSpacing: 0.4, textTransform: 'uppercase', width: 80, flexShrink: 0 }}>{label}</div>
      <div style={{ fontSize: 13, color: T.text, fontWeight: 400 }}>{value}</div>
    </div>
  );
}

function ModelsTable() {
  const rows = [
    { name: 'EfficientNet-B0', size: '15.4 MB', kind: 'image · letters' },
    { name: 'MLP Landmark', size: '0.23 MB', kind: 'landmark · letters' },
    { name: 'BiLSTM Single', size: '5.6 MB', kind: 'landmark · words' },
    { name: 'BiLSTM Ensemble (×5)', size: '27.8 MB', kind: 'landmark · words' },
  ];
  return (
    <div style={{ marginTop: 18 }}>
      <div style={{
        fontSize: 11, color: T.textTer, letterSpacing: 0.6,
        textTransform: 'uppercase', fontWeight: 500,
        margin: '0 4px 8px',
      }}>Models</div>
      <div style={{
        border: `1px solid ${T.cardBorder}`, borderRadius: 16,
        background: T.bg, overflow: 'hidden',
      }}>
        {rows.map((r, i) => (
          <div key={r.name} style={{
            display: 'flex', alignItems: 'center',
            padding: '12px 16px',
            borderBottom: i < rows.length - 1 ? `1px solid ${T.divider}` : 'none',
          }}>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: 13, fontWeight: 500, color: T.text, lineHeight: 1.3 }}>{r.name}</div>
              <div style={{ fontSize: 11, color: T.textSec, marginTop: 2, letterSpacing: 0.2 }}>{r.kind}</div>
            </div>
            <div style={{ fontFamily: MONO, fontSize: 12, color: T.textSec, fontVariantNumeric: 'tabular-nums' }}>{r.size}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// SCREEN 2 — Letters tab
// Camera (top 2/3) + results panel (bottom 1/3)
// ─────────────────────────────────────────────────────────────
function LettersScreen({ noHand = false }) {
  return (
    <Phone scroll={false}>
      <div style={{ display: 'flex', flexDirection: 'column', height: '100%', position: 'relative' }}>
        <AppBar title="Letters" />

        <div style={{ flex: 1, position: 'relative', overflow: 'hidden' }}>
          {/* Camera preview */}
          <CameraSurface noHand={noHand} mode="letters" />

          {/* Results panel - anchored bottom, overlapping into camera with rounded top corners */}
          <div style={{
            position: 'absolute', left: 0, right: 0, bottom: 0,
            height: 260,
            background: T.bg,
            borderRadius: '24px 24px 0 0',
            boxShadow: '0 -2px 12px rgba(16,20,24,0.06)',
            padding: '20px 20px 16px',
            boxSizing: 'border-box',
          }}>
            {noHand ? (
              <NoHandResults />
            ) : (
              <ResultsPanel
                caption="Top-3 predictions"
                rows={[
                  { label: 'L', conf: 0.94 },
                  { label: 'I', conf: 0.04 },
                  { label: 'V', conf: 0.01 },
                ]}
              />
            )}
          </div>
        </div>

        <BottomNav active="letters" />
      </div>
    </Phone>
  );
}

// ─────────────────────────────────────────────────────────────
// SCREEN 3 — Words tab
// ─────────────────────────────────────────────────────────────
function WordsScreen() {
  return (
    <Phone scroll={false}>
      <div style={{ display: 'flex', flexDirection: 'column', height: '100%', position: 'relative' }}>
        <AppBar title="Words" />

        <div style={{ flex: 1, position: 'relative', overflow: 'hidden' }}>
          <CameraSurface mode="words" />

          <div style={{
            position: 'absolute', left: 0, right: 0, bottom: 0,
            height: 280,
            background: T.bg,
            borderRadius: '24px 24px 0 0',
            boxShadow: '0 -2px 12px rgba(16,20,24,0.06)',
            padding: '18px 20px 16px',
            boxSizing: 'border-box',
          }}>
            <div style={{
              fontSize: 11, color: T.textTer, marginBottom: 10,
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            }}>
              <span style={{ letterSpacing: 0.4, textTransform: 'uppercase', fontWeight: 500 }}>Top-3 predictions</span>
              <span style={{ fontSize: 11, color: T.textSec, fontWeight: 400, textTransform: 'none', letterSpacing: 0.1 }}>updates every 3 frames</span>
            </div>
            <ResultsPanel
              hideCaption
              rows={[
                { label: 'thank you', conf: 0.87 },
                { label: 'hello', conf: 0.09 },
                { label: 'name', conf: 0.03 },
              ]}
            />
          </div>
        </div>

        <BottomNav active="words" />
      </div>
    </Phone>
  );
}

// ─────────────────────────────────────────────────────────────
// Camera surface — preview + skeleton + chips
// ─────────────────────────────────────────────────────────────
function CameraSurface({ noHand = false, mode = 'letters' }) {
  return (
    <div style={{
      position: 'absolute', inset: 0,
      background: 'linear-gradient(180deg, #2A2F33 0%, #1A1D20 60%, #131517 100%)',
      overflow: 'hidden',
    }}>
      {/* fake camera scene — soft vignette circle to suggest space */}
      <div style={{
        position: 'absolute', inset: 0,
        background: 'radial-gradient(ellipse 60% 50% at 50% 45%, rgba(160,170,180,0.18) 0%, rgba(0,0,0,0) 70%)',
      }} />
      {/* subtle grain */}
      <div style={{
        position: 'absolute', inset: 0, opacity: 0.06,
        backgroundImage: 'radial-gradient(rgba(255,255,255,0.6) 1px, transparent 1px)',
        backgroundSize: '3px 3px',
      }} />

      {/* Hand skeleton (only when not noHand) */}
      {!noHand && <HandSkeleton mode={mode} />}

      {/* FPS badge — top-right */}
      <div style={{
        position: 'absolute', top: 16, right: 16,
        padding: '6px 12px', borderRadius: 100,
        background: T.teal, color: '#fff',
        fontFamily: MONO, fontSize: 12, fontWeight: 500,
        letterSpacing: 0.3,
        boxShadow: '0 2px 8px rgba(0,137,123,0.4)',
        display: 'flex', alignItems: 'center', gap: 6,
      }}>
        {React.cloneElement(Icons.bolt, { size: 12, color: '#fff' })}
        <span>{mode === 'letters' ? '32 FPS · 8 ms' : '24 FPS · 14 ms'}</span>
      </div>

      {/* Model toggle — top-left */}
      <SegmentedToggle
        options={mode === 'letters'
          ? ['EfficientNet', 'MLP']
          : ['LSTM Single', 'LSTM Ensemble']}
        active={0}
      />

      {/* Buffer ring (words only) — bottom-left, above panel */}
      {mode === 'words' && (
        <div style={{
          position: 'absolute', left: 18, bottom: 296,
          display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6,
        }}>
          <BufferRing value={22} max={32} />
          <div style={{
            fontFamily: MONO, fontSize: 11, color: '#fff',
            background: 'rgba(0,0,0,0.55)', padding: '3px 9px', borderRadius: 100,
            letterSpacing: 0.2,
          }}>Buffer: 22/32</div>
        </div>
      )}

      {/* Soft fade from camera to white at the panel boundary */}
      <div style={{
        position: 'absolute', left: 0, right: 0, bottom: (mode === 'words' ? 280 : 260),
        height: 40, pointerEvents: 'none',
        background: 'linear-gradient(180deg, rgba(255,255,255,0) 0%, rgba(255,255,255,0.18) 100%)',
      }} />

      {/* "no hand" guidance overlay */}
      {noHand && (
        <div style={{
          position: 'absolute', left: 0, right: 0, top: '38%',
          textAlign: 'center', color: 'rgba(255,255,255,0.55)',
          fontSize: 13, letterSpacing: 0.2,
        }}>
          <div style={{
            display: 'inline-flex', flexDirection: 'column', alignItems: 'center', gap: 10,
          }}>
            <div style={{
              width: 56, height: 56, borderRadius: 28,
              border: '1.5px dashed rgba(255,255,255,0.35)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              {React.cloneElement(Icons.hand, { size: 28, color: 'rgba(255,255,255,0.55)' })}
            </div>
            <div>No hand in frame</div>
          </div>
        </div>
      )}
    </div>
  );
}

function SegmentedToggle({ options, active = 0 }) {
  return (
    <div style={{
      position: 'absolute', top: 14, left: 16,
      display: 'flex', borderRadius: 100, overflow: 'hidden',
      background: 'rgba(20,24,28,0.55)', backdropFilter: 'blur(8px)',
      border: `1px solid ${T.teal}`,
      padding: 3,
      fontSize: 12, fontWeight: 500,
    }}>
      {options.map((opt, i) => (
        <div key={opt} style={{
          padding: '5px 12px',
          borderRadius: 100,
          background: i === active ? T.teal : 'transparent',
          color: i === active ? '#fff' : 'rgba(255,255,255,0.75)',
          letterSpacing: 0.2,
          fontSize: 11.5,
        }}>{opt}</div>
      ))}
    </div>
  );
}

function BufferRing({ value, max }) {
  const r = 18; const c = 2 * Math.PI * r;
  const pct = value / max;
  const filled = pct >= 1;
  return (
    <div style={{ position: 'relative', width: 44, height: 44 }}>
      <svg width={44} height={44} viewBox="0 0 44 44">
        <circle cx="22" cy="22" r={r} fill="rgba(0,0,0,0.5)" stroke="rgba(255,255,255,0.2)" strokeWidth="3" />
        <circle cx="22" cy="22" r={r} fill="none"
          stroke={T.teal} strokeWidth="3" strokeLinecap="round"
          strokeDasharray={`${pct * c} ${c}`}
          transform="rotate(-90 22 22)" />
        {filled && <circle cx="22" cy="22" r={r - 5} fill={T.teal} />}
      </svg>
      <div style={{
        position: 'absolute', inset: 0,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        color: '#fff', fontFamily: MONO, fontSize: 10, fontWeight: 500,
      }}>{value}</div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// Hand skeleton — 21 MediaPipe landmarks
// Plausible hand pose, teal lines + dots
// ─────────────────────────────────────────────────────────────
function HandSkeleton({ mode = 'letters' }) {
  // Landmarks: wrist + 4 per finger (thumb, index, mid, ring, pinky)
  // Positions tuned to look like a recognizable open hand for "letters"
  // and a more dynamic mid-motion pose for "words".
  const lettersPose = [
    [196, 460], // 0 wrist
    // thumb (1-4)
    [148, 432], [120, 402], [102, 372], [92, 348],
    // index (5-8)
    [168, 380], [158, 320], [152, 274], [148, 236],
    // middle (9-12)
    [198, 372], [200, 304], [202, 254], [204, 212],
    // ring (13-16)
    [228, 380], [232, 318], [236, 268], [238, 228],
    // pinky (17-20)
    [256, 396], [266, 342], [274, 302], [280, 270],
  ];
  const wordsPose = [
    [206, 460],
    [156, 438], [126, 410], [104, 380], [90, 354],
    [176, 384], [170, 330], [180, 296], [196, 270],
    [206, 376], [212, 320], [228, 286], [248, 264],
    [232, 384], [248, 332], [266, 308], [284, 290],
    [256, 400], [276, 360], [290, 336], [302, 318],
  ];
  const lm = mode === 'words' ? wordsPose : lettersPose;
  const edges = [
    [0,1],[1,2],[2,3],[3,4],
    [0,5],[5,6],[6,7],[7,8],
    [5,9],[9,10],[10,11],[11,12],
    [9,13],[13,14],[14,15],[15,16],
    [13,17],[17,18],[18,19],[19,20],
    [0,17],
  ];
  return (
    <svg width="100%" height="100%" viewBox="0 0 412 580" style={{ position: 'absolute', inset: 0, pointerEvents: 'none' }}>
      {/* edges */}
      {edges.map(([a,b], i) => (
        <line key={i}
          x1={lm[a][0]} y1={lm[a][1]} x2={lm[b][0]} y2={lm[b][1]}
          stroke={T.teal} strokeWidth="2.4" strokeOpacity="0.92" strokeLinecap="round" />
      ))}
      {/* points */}
      {lm.map(([x, y], i) => (
        <g key={i}>
          <circle cx={x} cy={y} r={i === 0 ? 6 : 4.2} fill={T.teal} />
          <circle cx={x} cy={y} r={i === 0 ? 9 : 6} fill={T.teal} fillOpacity="0.18" />
        </g>
      ))}
    </svg>
  );
}

// ─────────────────────────────────────────────────────────────
// Results panel — top-3 rows with confidence bars
// ─────────────────────────────────────────────────────────────
function ResultsPanel({ caption, rows, hideCaption }) {
  return (
    <div>
      {!hideCaption && (
        <div style={{
          fontSize: 11, color: T.textTer, letterSpacing: 0.4,
          textTransform: 'uppercase', fontWeight: 500, marginBottom: 14,
        }}>{caption}</div>
      )}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
        {rows.map((r, i) => (
          <ConfRow key={r.label} {...r} rank={i + 1} />
        ))}
      </div>
    </div>
  );
}

function ConfRow({ label, conf, rank }) {
  const top = rank === 1;
  const pct = Math.round(conf * 100);
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 14,
    }}>
      <div style={{
        fontSize: top ? 22 : 16,
        fontWeight: top ? 600 : 500,
        color: top ? T.text : T.textSec,
        width: top ? 92 : 76,
        flexShrink: 0,
        letterSpacing: -0.2,
        lineHeight: 1,
      }}>{label}</div>
      <div style={{
        flex: 1, height: top ? 10 : 6, background: T.tealSoft,
        borderRadius: 100, overflow: 'hidden',
      }}>
        <div style={{
          width: `${pct}%`, height: '100%',
          background: top ? T.teal : T.tealContainer,
          borderRadius: 100,
        }} />
      </div>
      <div style={{
        fontFamily: MONO,
        fontSize: top ? 14 : 12,
        fontWeight: 500,
        color: top ? T.text : T.textSec,
        width: 44, textAlign: 'right',
        fontVariantNumeric: 'tabular-nums',
      }}>{pct}%</div>
    </div>
  );
}

function NoHandResults() {
  return (
    <div style={{
      height: '100%', display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center', gap: 14,
      paddingBottom: 20,
    }}>
      <div style={{
        width: 56, height: 56, borderRadius: 28,
        background: T.surface, color: T.textTer,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
      }}>
        {React.cloneElement(Icons.hand, { size: 28 })}
      </div>
      <div style={{ fontSize: 15, color: T.textSec, fontWeight: 500 }}>Show your hand to the camera</div>
      <div style={{ fontSize: 12, color: T.textTer, marginTop: -8 }}>Waiting for landmarks…</div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// SCREEN 4 (variant) — Permission denied
// ─────────────────────────────────────────────────────────────
function PermissionScreen() {
  return (
    <Phone scroll={false}>
      <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
        <AppBar title="Letters" />

        <div style={{
          flex: 1, display: 'flex', flexDirection: 'column',
          alignItems: 'center', justifyContent: 'center',
          padding: '40px 32px', textAlign: 'center', gap: 20,
        }}>
          <div style={{
            width: 96, height: 96, borderRadius: 48,
            background: T.surface, color: T.textTer,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            marginBottom: 4,
          }}>
            {React.cloneElement(Icons.cameraOff, { size: 44, stroke: 1.6 })}
          </div>
          <div>
            <h2 style={{
              fontSize: 22, fontWeight: 500, color: T.text,
              margin: '0 0 8px', letterSpacing: -0.2,
            }}>Camera access is required</h2>
            <p style={{
              fontSize: 14, color: T.textSec, lineHeight: 1.55, margin: 0,
              maxWidth: 280, textWrap: 'pretty',
            }}>This demo runs entirely on-device. Frames are processed locally and never leave your phone.</p>
          </div>
          <button style={{
            background: T.teal, color: '#fff', border: 'none',
            padding: '12px 24px', borderRadius: 100,
            fontSize: 14, fontWeight: 500, letterSpacing: 0.2,
            boxShadow: '0 1px 2px rgba(0,137,123,0.3), 0 4px 12px -4px rgba(0,137,123,0.3)',
            cursor: 'pointer', marginTop: 4,
          }}>Grant permission</button>
        </div>

        <BottomNav active="letters" />
      </div>
    </Phone>
  );
}

// ─────────────────────────────────────────────────────────────
// Expose to design canvas
// ─────────────────────────────────────────────────────────────
Object.assign(window, {
  HomeScreen, LettersScreen, WordsScreen, PermissionScreen,
});
