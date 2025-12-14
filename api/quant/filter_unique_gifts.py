#!/usr/bin/env python3
"""Filter unique gifts from Quant Marketplace and keep TGMRKT special gifts"""

import json

# The mapping you provided
EXISTING_GIFTS = {
    "5983471780763796287": "Santa Hat",
    "5936085638515261992": "Signet Ring",
    "5933671725160989227": "Precious Peach",
    "5936013938331222567": "Plush Pepe",
    "5913442287462908725": "Spiced Wine",
    "5915502858152706668": "Jelly Bunny",
    "5915521180483191380": "Durov's Cap",
    "5913517067138499193": "Perfume Bottle",
    "5882125812596999035": "Eternal Rose",
    "5882252952218894938": "Berry Box",
    "5857140566201991735": "Vintage Cigar",
    "5846226946928673709": "Magic Potion",
    "5845776576658015084": "Kissed Frog",
    "5825801628657124140": "Hex Pot",
    "5825480571261813595": "Evil Eye",
    "5841689550203650524": "Sharp Tongue",
    "5841391256135008713": "Trapped Heart",
    "5839038009193792264": "Skull Flower",
    "5837059369300132790": "Scared Cat",
    "5821261908354794038": "Spy Agaric",
    "5783075783622787539": "Homemade Cake",
    "5933531623327795414": "Genie Lamp",
    "6028426950047957932": "Lunar Snake",
    "6003643167683903930": "Party Sparkler",
    "5933590374185435592": "Jester Hat",
    "5821384757304362229": "Witch Hat",
    "5915733223018594841": "Hanging Star",
    "5915550639663874519": "Love Candle",
    "6001538689543439169": "Cookie Heart",
    "5782988952268964995": "Desk Calendar",
    "6001473264306619020": "Jingle Bells",
    "5980789805615678057": "Snow Mittens",
    "5836780359634649414": "Voodoo Doll",
    "5841632504448025405": "Mad Pumpkin",
    "5825895989088617224": "Hypno Lollipop",
    "5782984811920491178": "B-Day Candle",
    "5935936766358847989": "Bunny Muffin",
    "5933629604416717361": "Astral Shard",
    "5837063436634161765": "Flying Broom",
    "5841336413697606412": "Crystal Ball",
    "5821205665758053411": "Eternal Candle",
    "5936043693864651359": "Swiss Watch",
    "5983484377902875708": "Ginger Cookie",
    "5879737836550226478": "Mini Oscar",
    "5170594532177215681": "Lol Pop",
    "5843762284240831056": "Ion Gem",
    "5936017773737018241": "Star Notepad",
    "5868659926187901653": "Loot Bag",
    "5868348541058942091": "Love Potion",
    "5868220813026526561": "Toy Bear",
    "5868503709637411929": "Diamond Ring",
    "5167939598143193218": "Sakura Flower",
    "5981026247860290310": "Sleigh Bell",
    "5897593557492957738": "Top Hat",
    "5856973938650776169": "Record Player",
    "5983259145522906006": "Winter Wreath",
    "5981132629905245483": "Snow Globe",
    "5846192273657692751": "Electric Skull",
    "6023752243218481939": "Tama Gadget",
    "6003373314888696650": "Candy Cane",
    "5933793770951673155": "Neko Helmet",
    "6005659564635063386": "Jack-in-the-Box",
    "5773668482394620318": "Easter Egg",
    "5870661333703197240": "Bonded Ring",
    "6023917088358269866": "Pet Snake",
    "6023679164349940429": "Snake Box",
    "6003767644426076664": "Xmas Stocking",
    "6028283532500009446": "Big Year",
    "6003735372041814769": "Holiday Drink",
    "5859442703032386168": "Gem Signet",
    "5897581235231785485": "Light Sword",
    "5870784783948186838": "Restless Jar",
    "5870720080265871962": "Nail Bracelet",
    "5895328365971244193": "Heroic Helmet",
    "5895544372761461960": "Bow Tie",
    "5868455043362980631": "Heart Locket",
    "5871002671934079382": "Lush Bouquet",
    "5933543975653737112": "Whip Cupcake",
    "5870862540036113469": "Joyful Bundle",
    "5868561433997870501": "Cupid Charm",
    "5868595669182186720": "Valentine Box",
    "6014591077976114307": "Snoop Dogg",
    "6012607142387778152": "Swag Bag",
    "6012435906336654262": "Snoop Cigar",
    "6014675319464657779": "Low Rider",
    "6014697240977737490": "Westside Sign",
    "6042113507581755979": "Stellar Rocket",
    "6005880141270483700": "Jolly Chimp",
    "5998981470310368313": "Moon Pendant",
    "5933937398953018107": "Ionic Dryer",
    "5870972044522291836": "Input Key",
    "5895518353849582541": "Mighty Arm",
    "6005797617768858105": "Artisan Brick",
    "5960747083030856414": "Clover Pin",
    "5870947077877400011": "Sky Stilettos",
    "5895603153683874485": "Fresh Socks",
    "6006064678835323371": "Happy Brownie",
    "5900177027566142759": "Ice Cream",
    "5773725897517433693": "Spring Basket",
    "6005564615793050414": "Instant Ramen",
    "6003456431095808759": "Faith Amulet",
    "5935877878062253519": "Mousse Cake",
    "5902339509239940491": "Bling Binky",
    "5963238670868677492": "Money Pot",
    "5933737850477478635": "Pretty Posy"
}

# The 6 special TGMRKT gifts (with numeric IDs as names)
SPECIAL_MRKT_GIFTS = [
    "5775955135867913556",  # Gravestone
    "5776227780391864916",  # Coffin
    "5775966332847654507",  # Mask
    "6001229799790478558",  # Durov's Boots
    "6001425315291727333",  # Durov's Coat
    "6003477390536213997",  # Durov's Figurine
]

def filter_gifts():
    """Filter unique gifts from Quant Marketplace"""
    
    # Load Quant Marketplace gifts
    with open('quant_api_gifts.json', 'r', encoding='utf-8') as f:
        quant_gifts = json.load(f)
    
    print(f"📊 Total Quant Marketplace gifts: {len(quant_gifts)}")
    print(f"📊 Existing gifts to filter out: {len(EXISTING_GIFTS)}")
    print(f"📊 Special TGMRKT gifts to keep: {len(SPECIAL_MRKT_GIFTS)}\n")
    
    # Filter out gifts that exist in the provided mapping
    unique_gifts = []
    filtered_out = []
    special_kept = []
    
    for gift in quant_gifts:
        gift_id = gift.get('id', '')
        
        # Keep special TGMRKT gifts
        if gift_id in SPECIAL_MRKT_GIFTS:
            unique_gifts.append(gift)
            special_kept.append(f"{gift_id} - {gift.get('full_name', 'N/A')}")
            continue
        
        # Filter out if exists in the mapping
        if gift_id in EXISTING_GIFTS:
            filtered_out.append(f"{gift_id} - {gift.get('full_name', 'N/A')}")
        else:
            unique_gifts.append(gift)
    
    # Display results
    print("=" * 80)
    print(f"\n✅ SPECIAL TGMRKT GIFTS KEPT ({len(special_kept)}):\n")
    for item in special_kept:
        print(f"   • {item}")
    
    print(f"\n❌ FILTERED OUT ({len(filtered_out)}):\n")
    for item in filtered_out[:10]:  # Show first 10
        print(f"   • {item}")
    if len(filtered_out) > 10:
        print(f"   ... and {len(filtered_out) - 10} more")
    
    print(f"\n✨ UNIQUE QUANT GIFTS KEPT ({len(unique_gifts) - len(special_kept)}):\n")
    unique_only = [g for g in unique_gifts if g.get('id') not in SPECIAL_MRKT_GIFTS]
    for gift in unique_only[:10]:  # Show first 10
        print(f"   • {gift.get('id')} - {gift.get('full_name', 'N/A')}")
    if len(unique_only) > 10:
        print(f"   ... and {len(unique_only) - 10} more")
    
    print("\n" + "=" * 80)
    print(f"\n📊 SUMMARY:")
    print(f"   • Total gifts in Quant API: {len(quant_gifts)}")
    print(f"   • Special TGMRKT gifts kept: {len(special_kept)}")
    print(f"   • Unique Quant gifts kept: {len(unique_only)}")
    print(f"   • Filtered out (duplicates): {len(filtered_out)}")
    print(f"   • TOTAL IN CLEAN FILE: {len(unique_gifts)}")
    
    # Save clean file
    output_file = 'clean_unique_gifts.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(unique_gifts, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Saved clean file to: {output_file}")
    
    return unique_gifts

if __name__ == '__main__':
    filter_gifts()
