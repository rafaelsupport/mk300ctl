"""Catálogo da MK-300 (firmware 070), montado a partir dos prints do app M-EFCS.
Índice da lista = valor do byte effunit. Nomes de parâmetro só para combinações confirmadas."""

TYPES = {
    "FX": ["Wah-Wah", "Lofi", "Sense-Wah", "Boost", "A Boost", "E Boost", "B Boost", "Boost ED",
           "Compress", "Compress Pro", "F Compress", "Pitch", "Octave", "Ring", "Pitch shifter", "Whammy"],
    "DLY": ["Clean", "Modern", "Echo", "Analog", "Duck", "Dtype", "Tremolo", "Filter", "Dual", "Lofi",
            "Pattern", "Ice", "Reverse", "PingPong Stereo", "Clean Stereo", "Modern Stereo", "Echo Stereo",
            "Analog Stereo", "Duck Stereo", "Dtype Stereo", "Tremolo Stereo", "Filter Stereo", "Dual Stereo",
            "Lofi Stereo", "Pattern Stereo", "Ice Stereo", "Reverse Stereo"],
    "REV": ["Room", "Hall", "Plate", "Spring", "Shimmer", "Bloom", "Cloud", "Lofi", "Swell",
            "Room stereo", "Hall stereo", "Plate stereo", "Spring stereo", "Shimmer stereo",
            "Bloom stereo", "Cloud stereo", "Lofi stereo", "Swell stereo"],
    # Nomes de AMP vêm da memória do pedal (podem ser substituídos por importação); esta é a lista de fábrica.
    "AMP": """J120_CL J900_OD J900_DS J900_HV M_BLUES HORIZON M-VAVE_DS ROOM40 FD1_BR JOY_OD
M-VAVE_TS3 MT100_LEAD RAT_CL RAT_CR RAT_DS MES_RED FD_CH1 FD_CH1_HOT MT80_CL M_SUPER_OD
J800_CL_1960 J800_CL_AMP J800_OD J800_DS JOHNS_CH1 DARK_OD DARK_OD2 DARK_DS VXO_CL VXO_OD
VXO_OD2 VXO_OD3 OR_CL OR_CRUNCH HIGIAN HIGIAN_RED COOL_CL JVMcrunch JV410_BOOST AXE
MES_CH1 M-VAVE_DS3 M-VAVE_DS4 M-VAVE_LEAD LANY_CH1 LANY_CH1_BR LANY_CH2_OD LANY_CH3_DS ROLANS_CL ROLANS_DS
ROLANS_TDS BOOSS_METEL J900_CH1 J900_CH2 JVM_OD_FG JVM_DS_FG RADAL_CL_FG RADAL_DS RADAL_TDS RADAL_HDS
DUMBLE_FG JAZZ_OD M-VAVE_TS1 M-VAVE_TS2 EHV5150_CH1 EHV5150_CH2 EHV5150_DS EHV5150_MT XC_CL XC_OD
XC_DS XC_HV J2000_CL_FG J2000_CR_FG J2000_TR_FG J2000_DS_FG J900_CL_57 J900_DS_57 MAR_METEL MAR_HV
WS_JZCL_57 OR_CL_ECM OR_CRUNCH OR_SWEET BOG_LEAD BOG_LEAD2 BOG_LEAD3 BOG_SOLO MATTER_DS UK_DS
JHS_DS JHS_TDS M-VAVE_HOT M-VAVE_RED M-VAVE_MT M-VAVE_BST MES_CH2_57 MES_CH2_AMP MES_CH3_57 MES_CH3_AM
AgDb750_BS ApSVT_BS DgM900_BS FenRum_BS GkF550_BS HkeHd50_BS MarkLm_BS OrgAd_BS PjBuddy_BS RolDb_BS
Mb400C1_BS Mb400C2_BS DgXu_BS ApSp_BS Mar50_BS Mark500_BS PjbCub_BS Tc21Vt_BS WatMod_BS GKL800_BS""".split(),
}

TYPES["DS"] = """BLUES_OD TS8 DS1 DS2 M-VAVE_OD M-VAVE_DS M-VAVE_TS1 M-VAVE_TS2 SUPA_1 SUPA_2
RAT RAT_BT JHS_1 JHS_2 MT_1 MT_2 TDS XC_DS QC_DS HIGAIN
M-BOOSTER TS-9 BIG-DR CL_BOOST BD M90S M2000 DS800 DS900 MAR-DS
BOG_DS SONDO MID-BOST RED_DS MODEN_DS SuperOD BLUES_DR Black-BOX BIG-MUFF PLX""".split()

# CAB: 26-100 do encarte da caixa; 1-25 só os que aparecem na tabela de presets de fábrica (None = desconhecido)
_cab_low = {1: "AC-SeVin", 2: "JVM_1960_57", 3: "JVM_G12_ECM", 4: "DELUXE_REV", 5: "BOG_57",
            9: "HIW412SWF", 10: "MAR1960_412", 12: "MESA_412_ECM", 13: "WANGS112_ECM",
            15: "V30_MC834", 16: "V30_MD421", 17: "VOX_AC30", 22: "M160_Center", 25: "Chug_R"}
_cab_high = """EV_MIX_B G12-EVH G12-EVH_CT G12-EVH_i5 G12-EVH_m160 Marshall_Box BGN412V30 MESA_LS MESA_CS MESA_HS
Recto_112 FRMAN112 OR_112 HIFI_OK Ranli_412 OR_V30_212 OR_G75_212 RE_SUPER_412 EGNL01_412 EGNL02_412
EGNL03_412 MeOSick-II MeOSick-III MesaOSick-I SoldHor SoldSC412 AC-SeTV20 Pey5150 MRSH03 VA5153
AC-EmG212 AC-Se210 CeleAt AC-SeGol AC-CateEx AC-CateFw DieV30 EAGLProV30s Sperimental Peavey115
Peavey112 VxAc15 FimanVt FenDeluX FenProJ Alton212 OgP412 OgV30 HaBtonV MarMfour
Elctrovoice J120Rolnd MessOS Mar60AV WS212_57 Agula410 AmpgSVT410 AmpgSVT810 AshB115 Bareface110
Bstert115 DavEendD410 DgD210C DgDG212N FdBman410 FdBmanSf210 GKRB410A GKRB410B Hark410 MbSubway210
OgOBC212 Pey115 RanRB100 SR115 Tace412""".split()
TYPES["CAB"] = [_cab_low.get(n) for n in range(1, 26)] + _cab_high   # índice 0 = CAB nº 1

TYPES["WAH"] = ["X-Wah", "Funk-Wah", "Slide-Wah", "Cry-Wah", "Wah-Wah", "Sense-Wah"]
TYPES["GATE"] = ["AI Gate", "Soft Gate", "Hard Gate", "Pro Gate", "Compress", "Compress Pro", "F Compress", "AI Ms Gate"]
TYPES["EQ"] = ["Guitar EQ 6", "Bass EQ 7", "Normal EQ 10"]
TYPES["MOD"] = ["Chorus", "Tri Chorus", "Flanger", "Tri Flanger", "Tremolo", "Tri Tremolo", "Opto Tremolo",
                "Phaser", "Vibrato", "Tri Vibrato", "Opto Vibrato", "Univibe", "Tri Univibe", "Autofilter",
                "Phaser Stereo", "Flanger Stereo", "Vibe Stereo", "Chorus Stereo", "Tremolo Stereo", "Vibrato Stereo"]

# (módulo, tipo) -> nomes dos parâmetros; tipo None = vale para todos os tipos do módulo
PARAMS = {
    ("AMP", None): ["Gain", "Level", "Bass", "Middle", "Treble", "Reso", "Pres", "Bright"],
    ("FX", 3): ["Gain", "Level"],                                   # Boost
    ("DLY", 0): ["Time", "Fb", "Mix", "Sync"],                      # Clean
    ("REV", 10): ["Decay", "Mix", "HighPass", "LowPass", "ModDepth"],  # Hall stereo
    ("VOL", None): ["Volume"],
}

# Ordem dos knobs como o app mostra (vídeos de 19/10). Confirmados contra dump: AMP, FX Boost, DLY Clean,
# REV Hall stereo, WAH X-Wah, GATE AI Gate, MOD Chorus. Os demais seguem a ordem da tela, sem dump ainda.
_wah_basic = ["Value", "Gain", "Level"]
_trem = ["Speed", "Depth", "Level", "Sync"]
_vib = ["Speed", "Depth", "Sync"]
_univ = ["Speed", "Depth", "Mix", "Sync"]
_flan = ["Speed", "Depth", "Fb", "Mix", "Sync"]
_cpro = ["Ratio", "Gain", "Knee", "Thd", "Attack", "Level", "Blend", "Detect"]
PARAMS.update({
    ("WAH", 0): _wah_basic, ("WAH", 1): _wah_basic, ("WAH", 2): _wah_basic, ("WAH", 3): _wah_basic,
    ("WAH", 4): ["Speed", "Q", "Mix", "Width", "Level", "Sync"],
    ("WAH", 5): ["Sense", "Attack", "Q", "fPeak", "Mix", "Width", "Level"],
    ("GATE", 0): ["Gate", "Bias", "Detect"], ("GATE", 7): ["Gate", "Bias", "Detect"],
    ("GATE", 1): ["Thd", "Detect"], ("GATE", 2): ["Thd", "Detect"],
    ("GATE", 3): ["Att", "Rel", "Thd", "Kw", "Ratio", "Detect"],
    ("GATE", 4): ["Sustain", "Attack", "Level", "Blend", "Detect"],
    ("GATE", 5): _cpro,
    ("GATE", 6): ["Ratio", "Gain", "Knee", "Thd", "Attack", "Tone", "Level", "Blend", "Detect"],
    ("EQ", 0): ["100Hz", "200Hz", "400Hz", "800Hz", "1.6kHz", "3.2kHz"],
    ("EQ", 1): ["50Hz", "120Hz", "400Hz", "500Hz", "800Hz", "4.5kHz", "10kHz"],
    ("EQ", 2): ["31Hz", "62Hz", "125Hz", "250Hz", "500Hz", "1kHz", "2kHz", "4kHz", "8kHz", "16kHz"],
    ("MOD", 0): _univ[:1] + ["Depth", "Mix", "Sync"], ("MOD", 1): ["Speed", "Depth", "Mix", "Sync"],
    ("MOD", 2): _flan, ("MOD", 3): _flan,
    ("MOD", 4): _trem, ("MOD", 5): _trem, ("MOD", 6): _trem,
    ("MOD", 7): ["Speed", "MidCut", "Reso", "Fb", "Sync"],
    ("MOD", 8): _vib, ("MOD", 9): _vib, ("MOD", 10): _vib,
    ("MOD", 11): _univ, ("MOD", 12): _univ,
    ("MOD", 13): ["Speed", "Min", "Max", "Mix", "Fb", "Sync"],
    ("MOD", 14): ["Speed", "Stage", "Regen", "Mix", "Lfo", "Sync"],
    ("MOD", 15): ["Speed", "Depth", "Regen", "Mix", "Jet", "Lfo", "Sync"],
    ("MOD", 16): ["Speed", "Stage", "Regen", "Mix", "Lfo", "Sync"],
    ("MOD", 17): ["Speed", "Depth", "Mode", "Mix", "Sync"],
    ("MOD", 18): ["Speed", "Depth", "Level", "Mode", "Sync"],
    ("MOD", 19): ["Speed", "Depth", "Bits", "Mix", "Sync"],
})


def type_name(mod, t):
    lst = TYPES.get(mod)
    return lst[t] if lst and 0 <= t < len(lst) and lst[t] else None


def param_names(mod, t):
    return PARAMS.get((mod, t)) or PARAMS.get((mod, None))
