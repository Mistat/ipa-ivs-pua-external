import fontforge
import os

ROOT_DIR = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
ORG_PATH = os.path.join(ROOT_DIR, 'fonts', 'ipam.ttf')
EXT_PATH = os.path.join(ROOT_DIR, 'fonts', 'ipa-ivs-external.ttf')

org_font = fontforge.open(ORG_PATH)
ext_font = fontforge.open(EXT_PATH)

SPACE_CODEPOINTS = {
    0x0020, 0x00A0, 0x1680,
    0x2000, 0x2001, 0x2002, 0x2003, 0x2004,
    0x2005, 0x2006, 0x2007, 0x2008, 0x2009,
    0x200A, 0x202F, 0x205F, 0x3000,
    0x0009
}

def font_list(font):
    print (f"Listing up to 10 glyphs without Unicode values in font: {font.fontname}")
    for glyph in font.glyphs():
        if glyph.glyphname.startswith("aj"):
            print(f"Glyph '{glyph.glyphname}' {glyph.unicode:#04x}")
            if  glyph.altuni:
                for altuni in glyph.altuni:
                    print(f"  altuni '{glyph.altuni}")


#font_list(org_font)
font_list(ext_font)