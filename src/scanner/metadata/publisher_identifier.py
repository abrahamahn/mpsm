"""Publisher identification from file paths and metadata."""

from pathlib import Path
from typing import Dict, List, Pattern
import re


# Publisher patterns - match company names in paths
PUBLISHER_PATTERNS: Dict[str, List[str]] = {
    # Major DAW Manufacturers
    'Steinberg': ['steinberg', 'cubase', 'nuendo'],
    'Avid': ['avid', 'pro tools', 'protools', 'sibelius'],
    'Image-Line': ['image-line', 'fl studio', 'flstudio', 'fruity'],
    'Ableton': ['ableton', 'live'],
    'PreSonus': ['presonus', 'studio one'],
    'Apple': ['apple', 'logic', 'mainstage', 'garageband'],
    'Propellerhead': ['propellerhead', 'reason'],
    'Bitwig': ['bitwig'],
    'Reaper': ['reaper', 'cockos'],
    'Cakewalk': ['cakewalk', 'sonar'],

    # Major Plugin Manufacturers
    'Native Instruments': ['native instruments', 'ni-racks', 'komplete', 'kontakt', 'massive'],
    'Spectrasonics': ['spectrasonics', 'omnisphere', 'trilian', 'keyscape'],
    'Waves': ['waves audio', 'waves'],
    'iZotope': ['izotope', 'ozone', 'neutron', 'rx'],
    'FabFilter': ['fabfilter'],
    'Arturia': ['arturia'],
    'Native Instruments': ['native instruments'],
    'Xfer Records': ['xfer', 'serum'],
    'Valhalla DSP': ['valhalla', 'valhalladsp'],
    'u-he': ['u-he', 'uhe', 'diva', 'zebra'],
    'Output': ['output'],
    'Soundtoys': ['soundtoys'],
    'Slate Digital': ['slate digital'],
    'Plugin Alliance': ['plugin alliance', 'brainworx'],
    'Kilohearts': ['kilohearts'],
    'PSPaudioware': ['pspaudioware', 'psp'],
    'Cytomic': ['cytomic', 'the glue'],
    'DMGAudio': ['dmgaudio'],
    'Softube': ['softube'],
    'Universal Audio': ['universal audio', 'uad'],
    'Eventide': ['eventide'],
    'Lexicon': ['lexicon'],
    'TC Electronic': ['tc electronic'],

    # Orchestral Libraries
    'Spitfire Audio': ['spitfire audio', 'spitfire'],
    'EastWest': ['eastwest', 'quantum leap'],
    'Vienna Symphonic Library': ['vienna', 'vsl'],
    '8Dio': ['8dio'],
    'Orchestral Tools': ['orchestral tools'],
    'ProjectSAM': ['projectsam'],

    # Synth Manufacturers
    'Lennar Digital': ['lennar digital', 'sylenth'],
    'Rob Papen': ['rob papen'],
    'Reveal Sound': ['reveal sound', 'spire'],
    'Tone2': ['tone2'],
    'Synapse Audio': ['synapse audio', 'dune'],
    'LennarDigital': ['lennardigital'],
    'Camel Audio': ['camel audio', 'alchemy'],

    # Amp Sims & Guitar
    'IK Multimedia': ['ik multimedia', 'amplitube'],
    'Positive Grid': ['positive grid', 'bias'],
    'Neural DSP': ['neural dsp'],
    'Line 6': ['line 6', 'helix'],
    'Overloud': ['overloud', 'th3'],

    # Mastering/Mixing
    'Ozone': ['ozone'],
    'T-RackS': ['t-racks', 'ik multimedia'],
    'Izotope': ['izotope'],
}


def identify_publisher_from_path(file_path: Path) -> str:
    """
    Identify publisher from file path.

    Args:
        file_path: Path to plugin file

    Returns:
        Publisher name or "Unknown"
    """
    path_str = str(file_path).lower()

    # Check each publisher pattern
    for publisher, patterns in PUBLISHER_PATTERNS.items():
        for pattern in patterns:
            if pattern.lower() in path_str:
                return publisher

    return "Unknown"


def identify_publisher_from_metadata(product_name: str, company_name: str = "") -> str:
    """
    Identify publisher from product metadata.

    Args:
        product_name: Product/plugin name
        company_name: Company name from PE header

    Returns:
        Publisher name or "Unknown"
    """
    search_text = f"{product_name} {company_name}".lower()

    # Check patterns
    for publisher, patterns in PUBLISHER_PATTERNS.items():
        for pattern in patterns:
            if pattern.lower() in search_text:
                return publisher

    # Return company name if provided
    if company_name and company_name.lower() != "unknown":
        return company_name

    return "Unknown"
