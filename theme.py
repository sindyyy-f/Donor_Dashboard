"""Earthy presentation for the donor dashboard."""
from contextlib import contextmanager

import streamlit as st


def apply_earth_theme():
    st.markdown('''
<style>
/* Remove Streamlit's top navigation chrome. */
[data-testid="stHeader"],
[data-testid="stSidebarNav"] { display: none !important; }

/* Hide the heading permalink icon in the hero. */
.earth-hero a[href^="#"],
.earth-hero [data-testid="stHeaderActionElements"],
.earth-hero .anchor-link { display: none !important; }

/* Keep all forecast text readable, including nested Streamlit elements. */
.st-key-earth_forecast,
.st-key-earth_forecast * {
    color: #173d29 !important;
    -webkit-text-fill-color: #173d29 !important;
}
.st-key-earth_forecast svg text { fill: #173d29 !important; }
.st-key-earth_forecast button[kind="secondary"],
.st-key-earth_forecast button[kind="secondary"]:hover {
    background: #d5e5c8 !important;
    border-color: #507c4b !important;
}

/* Explicit label colors override Streamlit's inherited widget text styles. */
.st-key-earth_forecast [data-testid="stWidgetLabel"],
.st-key-earth_forecast [data-testid="stWidgetLabel"] *,
.st-key-earth_forecast [data-testid="stSlider"] label,
.st-key-earth_forecast [data-testid="stSlider"] label *,
.st-key-earth_forecast [data-testid="stSelectbox"] label,
.st-key-earth_forecast [data-testid="stSelectbox"] label *,
.st-key-earth_forecast [data-testid="stRadio"] label,
.st-key-earth_forecast [data-testid="stRadio"] label *,
.st-key-earth_forecast [data-testid="stCheckbox"] label,
.st-key-earth_forecast [data-testid="stCheckbox"] label *,
.st-key-earth_forecast [data-baseweb="select"] [class*="value"],
.st-key-earth_forecast [data-testid="stThumbValue"] {
    color: #173d29 !important;
    -webkit-text-fill-color: #173d29 !important;
    opacity: 1 !important;
}
.st-key-earth_forecast [data-testid="stWidgetLabel"] p {
    font-weight: 600 !important;
}
/* Forecast controls use the same sage cards and forest-green accents. */
.st-key-earth_forecast [data-testid="stSlider"],
.st-key-earth_forecast [data-testid="stSelectbox"],
.st-key-earth_forecast [data-testid="stRadio"],
.st-key-earth_forecast [data-testid="stCheckbox"] {
    background: #f0f5e9; border: 1px solid #a4bc94; border-radius: 12px;
    padding: 14px 16px; color: #203b2c;
}
.st-key-earth_forecast [data-testid="stWidgetLabel"] p,
.st-key-earth_forecast [data-testid="stSliderTickBarMin"],
.st-key-earth_forecast [data-testid="stSliderTickBarMax"],
.st-key-earth_forecast [data-testid="stThumbValue"],
.st-key-earth_forecast [data-baseweb="radio"] p,
.st-key-earth_forecast [data-baseweb="checkbox"] p { color: #203b2c !important; }
.st-key-earth_forecast [data-baseweb="select"] > div {
    background: #fffcf5; color: #203b2c; border-color: #7c9e70; border-radius: 8px;
}
.st-key-earth_forecast [role="slider"] { background-color: #47745b !important; }
.st-key-earth_forecast [data-baseweb="slider"] > div > div { background: #7e9e69 !important; }
.st-key-earth_forecast input { accent-color: #47745b; }
.st-key-earth_forecast [data-baseweb="radio"]:has(input:checked) > div:first-child,
.st-key-earth_forecast [data-baseweb="checkbox"]:has(input:checked) > span:first-child {
    background-color: #47745b !important; border-color: #47745b !important;
}
.st-key-earth_forecast button[kind="secondary"] {
    background: #294d3b; color: #f0f5e9; border: 1px solid #294d3b;
    border-radius: 10px; padding: 8px 18px;
}
.st-key-earth_forecast button[kind="secondary"]:hover { background: #3d654c; color: #fff; }
.st-key-earth_forecast button:focus-visible,
.st-key-earth_forecast [role="slider"]:focus-visible { outline: 3px solid #789b60; outline-offset: 3px; }

.data-disclosure-footer {
    position: relative; left: 50%; transform: translateX(-50%);
    width: 100vw; box-sizing: border-box;
    margin-top: 36px; padding: 26px max(24px, calc((100vw - 1200px) / 2));
    background: #294d3b; border-top: 3px solid #8ba47b;
    color: #f0f5e9; text-align: center;
}
.data-disclosure-footer strong { font-size: 1rem; }
.data-disclosure-footer p { font-size: .9rem; line-height: 1.6; margin: 8px auto 0; max-width: 1000px; color: #f0f5e9; }
.block-container { padding-bottom: 0 !important; }
[data-testid="stMain"] { overflow-x: clip; }

/* Hide Streamlit hosting and application menu controls. */
[data-testid="stToolbar"],
[data-testid="stAppDeployButton"],
.stAppDeployButton,
#MainMenu { display: none !important; }

.chart-heading { min-height: 145px; }
.chart-heading h4 { font-size: 1.1rem; color: #254633; margin: 0 0 10px; padding: 0; }
.chart-heading p { font-size: .9rem; line-height: 1.5; color: #304b36; margin: 0; }
.chart-key { min-height: 155px; box-sizing: border-box; background: #e5eedc; border: 1px solid #8ba47b; border-radius: 10px; padding: 14px; color: #203b2c; font-size: .9rem; }
.chart-key strong { display: block; margin-bottom: 10px; }
.chart-key p { font-size: .9rem; line-height: 1.5; margin: 0 0 8px; }
.legend-dot { display: inline-block; width: 12px; height: 12px; border-radius: 50%; margin-right: 7px; border: 1px solid #ffffff; }
.legend-dot.active { background: #47745b; }
.legend-dot.risk { background: #af684b; }
.legend-dot.river { background: #4d8c89; }
@media (max-width: 640px) { .chart-heading { min-height: 0; margin-bottom: 16px; } .chart-key { min-height: 0; } }

[class*="st-key-earth_"] {
    position: relative; border: 1px solid #7c9e70 !important;
    border-top: 4px solid #507c4b !important; border-radius: 18px !important;
    background: linear-gradient(145deg, #e8f0df, #d6e5cb);
    padding: 22px !important; margin-bottom: 16px;
    box-shadow: 0 6px 18px #244b2720;
}
[class*="st-key-earth_chart_"] { padding: 14px !important; background: #f0f5e9; height: 100%; }
.section-leaves { position: absolute; top: -6px; right: 4px; width: 90px; height: 64px; overflow: hidden; pointer-events: none; opacity: .55; }
.section-leaves i { position: absolute; width: 12px; height: 20px; border-radius: 2px 85% 2px 85%; background: #678b45; animation: section-drift 8s linear infinite; }
.section-leaves i:nth-child(2) { left: 35px; background: #ac8545; animation-delay: -3s; }
.section-leaves i:nth-child(3) { left: 62px; background: #52794c; animation-delay: -6s; }
@keyframes section-drift { from { transform: translate(0,-25px) rotate(-30deg); } to { transform: translate(22px,80px) rotate(170deg); } }
@media (prefers-reduced-motion: reduce) { .section-leaves i { animation: none; top: 12px; transform: rotate(35deg); } }
@media (max-width: 640px) { [class*="st-key-earth_"] { padding: 14px !important; } }

.stApp { background: linear-gradient(135deg, #b8d0a6 0%, #94b58b 55%, #759c78 100%); color: #203b2c; }
[data-testid="stMain"] { position: relative; isolation: isolate; }
.block-container { position: relative; z-index: 1; }
.falling-canopy { position: fixed; inset: 0; z-index: -1; overflow: hidden; pointer-events: none; }
.falling-canopy span {
    position: absolute; top: -65px; left: var(--x);
    width: var(--size); height: var(--size); opacity: .55;
    animation: canopy-fall var(--duration) linear var(--delay) infinite;
}
.falling-canopy svg { width: 100%; height: 100%; overflow: visible; }
@keyframes canopy-fall {
    0% { transform: translate3d(-25px, -65px, 0) rotate(0deg); }
    35% { transform: translate3d(35px, 38vh, 0) rotate(110deg); }
    70% { transform: translate3d(-15px, 76vh, 0) rotate(235deg); }
    100% { transform: translate3d(40px, 115vh, 0) rotate(360deg); }
}
@media (prefers-reduced-motion: reduce) { .falling-canopy { display: none; } }
@media (max-width: 640px) { .falling-canopy span:nth-child(n+13) { display: none; } }
[data-testid="stHeader"] { background: rgba(184,208,166,.94); }
.block-container { max-width: 1440px; padding-top: 2rem; }
h1, h2, h3 { color: #294d3b; }
h2, h3 { font-family: Georgia, serif; }
[data-testid="stMetric"] {
    background: #fffcf5; border: 1px solid #dcdccc;
    border-top: 3px solid #7e9673; border-radius: 14px;
    padding: 20px 22px; box-shadow: 0 4px 14px #31453308;
    height: 100%;
}
[data-testid="stMetricLabel"] { color: #58644f; }
[data-testid="stMetricValue"] { color: #294d3b; }
[data-testid="stCaptionContainer"] { color: #304b36; }
[data-testid="stPlotlyChart"], [data-testid="stDataFrame"] {
    border: 1px solid #dcdccc; border-radius: 14px;
    overflow: hidden; background: #fffcf5;
}
[data-testid="stAlert"] { background: #e4ece0; color: #293d32; }
.earth-hero {
    position: relative; overflow: hidden; border-radius: 22px;
    background: #dfe8d8; min-height: 300px; margin-bottom: 26px;
    border: 1px solid #cbd8c2;
}
.earth-hero svg { position: absolute; width: 100%; height: 100%; inset: 0; }
.earth-hero-copy { position: relative; z-index: 1; padding: 34px 38px 115px; max-width: 720px; }
.earth-eyebrow { color: #46634c; font-size: .75rem; font-weight: 700; letter-spacing: .17em; text-transform: uppercase; }
.earth-hero h1 { font-family: Georgia, serif; font-size: clamp(1.8rem, 3.3vw, 3rem); line-height: 1.13; color: #254633; padding: 12px 0; margin: 0; }
.earth-hero .hero-tagline { margin-top: 14px; }
.earth-hero .hero-description { margin-top: 12px; line-height: 1.6; max-width: 660px; }
.earth-hero p { color: #425e48; margin: 0; font-size: .98rem; }
.river-current { stroke-dasharray: 55 95; animation: river-flow 9s linear infinite; }
@keyframes river-flow { to { stroke-dashoffset: -300; } }
@media (prefers-reduced-motion: reduce) { .river-current { animation: none; } }
@media (max-width: 640px) {
    .earth-hero-copy { padding: 25px 22px 125px; }
    .earth-hero { min-height: 340px; }
    [data-testid="stMetric"] { padding: 16px; }
}
</style>
<section class="earth-hero" aria-label="Forest landscape with a flowing river">
<svg viewBox="0 0 1400 340" preserveAspectRatio="xMidYMax slice" aria-hidden="true">
<defs>
  <linearGradient id="sky" x2="0" y2="1"><stop stop-color="#e4ebdc"/><stop offset="1" stop-color="#d2dfc8"/></linearGradient>
  <linearGradient id="water" x2="0.3" y2="1"><stop stop-color="#9dc3be"/><stop offset="1" stop-color="#4d8c89"/></linearGradient>
  <g id="fir"><path d="M-3 0H3V-92H-3Z" fill="#6c6b4e"/><path d="M0-150L-32-88H-20L-45-40H-28L-54-4H54L28-40H45L20-88H32Z" fill="currentColor"/></g>
</defs>
<path fill="url(#sky)" d="M0 0H1400V340H0Z"/>
<circle cx="1155" cy="65" r="39" fill="#f2e6b9"/>
<path d="M0 244Q200 157 420 220T820 210T1400 175V340H0Z" fill="#bdcfae"/>
<path d="M0 283Q230 214 440 265T860 245T1400 220V340H0Z" fill="#95b08b"/>
<path d="M1030 215C900 240 1170 257 990 279S740 305 890 340H1140C940 299 1230 280 1090 251S1000 233 1060 215Z" fill="url(#water)"/>
<g fill="none" stroke="#d5eeDE" stroke-width="2" opacity=".65" class="river-current">
<path d="M1044 226C965 241 1156 257 1046 279S843 305 1000 340"/>
<path d="M1040 246C1120 262 1013 275 943 292S906 314 968 329"/>
</g>
<g color="#789976"><use href="#fir" transform="translate(1260 260) scale(.9)"/><use href="#fir" transform="translate(1340 252) scale(.7)"/><use href="#fir" transform="translate(1188 255) scale(.63)"/></g>
<g color="#486f53"><use href="#fir" transform="translate(1320 322) scale(1.55)"/><use href="#fir" transform="translate(1210 310) scale(1.15)"/><use href="#fir" transform="translate(1390 335) scale(1.3)"/></g>
<path d="M0 312Q150 273 355 310T755 316L800 340H0Z" fill="#63845c"/>
<g color="#3d654c"><use href="#fir" transform="translate(45 338) scale(.9)"/><use href="#fir" transform="translate(115 330) scale(.65)"/></g>
<g fill="#a8ad85"><ellipse cx="823" cy="328" rx="22" ry="8"/><ellipse cx="1161" cy="329" rx="30" ry="10"/></g>
</svg>
<div class="earth-hero-copy">
<div class="earth-eyebrow">Rooted in community</div>
<h1>Environmental Nonprofit Donor Engagement &amp; Retention Dashboard</h1>
<p class="hero-description">This dashboard helps an environmental nonprofit monitor donation activity, understand donor engagement, identify donors who may be at risk of disengaging, and forecast future donation growth.</p>
<p class="hero-tagline">A clearer view of the generosity that helps your community grow.</p>
</div>
</section>
''', unsafe_allow_html=True)
    leaf = '<svg viewBox="0 0 40 48" aria-hidden="true"><path d="M20 40C-3 34 3 12 31 3C39 24 33 39 20 40Z" fill="#aa743b"/><path d="M13 47L28 12M19 33L10 24M23 23L31 20" fill="none" stroke="#6e542e" stroke-width="2" stroke-linecap="round"/></svg>'
    green_leaf = leaf.replace('#aa743b', '#537b3e').replace('#6e542e', '#c1cf83')
    acorn = '<svg viewBox="0 0 40 48" aria-hidden="true"><path d="M8 21H32C33 34 25 41 20 45C14 41 7 34 8 21Z" fill="#b98246"/><path d="M5 23C3 7 36 6 35 23Z" fill="#6e4c2e"/><path d="M20 11Q18 4 25 2" fill="none" stroke="#59472c" stroke-width="4" stroke-linecap="round"/><path d="M13 15L17 20M21 14L25 20M29 16L31 20" stroke="#997448" stroke-width="2"/></svg>'
    pieces = []
    for i in range(24):
        art = (green_leaf, leaf, acorn)[i % 3]
        pieces.append(
            f'<span style="--x:{(i * 43 + 3) % 100}%;--size:{22 + (i % 4) * 5}px;'
            f'--duration:{18 + i % 7 * 2}s;--delay:-{i * 3 + 2}s">{art}</span>'
        )
    st.markdown('<div class="falling-canopy" aria-hidden="true">' + ''.join(pieces) + '</div>', unsafe_allow_html=True)
    st.caption("Overview of synthetic donor and donation data.")


def style_chart(figure):
    figure.update_layout(
        paper_bgcolor="#fffcf5", plot_bgcolor="#fffcf5",
        font=dict(family="Arial, sans-serif", color="#173d29", size=13),
        hoverlabel=dict(bgcolor="#fffcf5", font_color="#173d29"),
        title=dict(text="", font=dict(family="Georgia, serif", size=22, color="#173d29")),
        colorway=["#47745b", "#6d9e9b", "#af684b", "#a69a64", "#83996a"],
        margin=dict(t=75, b=45, l=35, r=35),
    )
    figure.update_xaxes(gridcolor="#e5e6d9", linecolor="#cdd5c6",
                        tickfont=dict(color="#173d29", size=12),
                        title_font=dict(color="#173d29", size=13))
    figure.update_yaxes(gridcolor="#e5e6d9", linecolor="#cdd5c6",
                        tickfont=dict(color="#173d29", size=12),
                        title_font=dict(color="#173d29", size=13))
    if figure.data and figure.data[0].type == "scatter":
        figure.update_traces(line_color="#4d8c89", line_width=3,
                             marker_color="#47745b", marker_size=8)


@contextmanager
def earth_section(key):
    """Group a dashboard section in a leafy, green Streamlit panel."""
    with st.container(border=True, key=f"earth_{key}"):
        st.markdown(
            '<div class="section-leaves" aria-hidden="true"><i></i><i></i><i></i></div>',
            unsafe_allow_html=True,
        )
        yield
