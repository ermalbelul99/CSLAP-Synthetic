import re

tex_path = 'c:/Users/ebelul/Downloads/CSLAP_Project_All/Computer&Industrial_Engineering.tex'
try:
    with open(tex_path, 'r', encoding='utf-8') as f:
        content = f.read()

    print("--- 1. Constraint 17 ---")
    con17_match = re.search(r'(sum_\{p.*?\\leq\s*T_s.*?)\\label\{con17\}', content, re.DOTALL)
    if con17_match:
        print(con17_match.group(0))

    print("\n--- 2. Logical OR {os}$ ---")
    if "logical OR" in content:
        print("Found 'logical OR' in text.")
        
    print("\n--- 4. CG Pricing Heuristic ---")
    if "pricing" in content.lower():
        pricing_idx = content.lower().find('pricing problem')
        print(content[pricing_idx:pricing_idx+1000])
        
    print("\n--- 8. Statistics ---")
    if "t-test" in content.lower() or "significant" in content.lower() or "sensitivity" in content.lower():
        print("Found keywords for stats/sensitivity:")
        for line in content.split('\n'):
            if "t-test" in line.lower() or "sensitivity" in line.lower():
                print(line)
                
    print("\n--- 10. Literature Review ---")
    lit_idx = content.find('\section{\textcolor{violet}{Literature Review}}')
    if lit_idx != -1:
        print(content[lit_idx:lit_idx+1500])

    print("\n--- 11. Introduction contribution ---")
    intro_idx = content.find('\section{Introduction}')
    if intro_idx != -1:
        print(content[intro_idx+1000:intro_idx+3000])

except Exception as e:
    print(e)
