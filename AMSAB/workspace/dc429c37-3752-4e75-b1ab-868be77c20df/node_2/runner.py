# AMSAB Worker — auto-generated runner
# Task: extract and organize recipe steps
# Tool: python_interpreter
import json, sys, os

ARGS = {
  "code": "node_1_output = \"\"\"{\"status\": \"ok\", \"output\": \"step-by-step biryani recipe at DuckDuckGo &nbsp; DuckDuckGo &nbsp; All Regions Argentina Australia Austria Belgium (fr) Belgium (nl) Brazil Bulgaria Canada (en) Canada (fr) Catalonia Chile China Colombia Croatia Czech Republic Denmark Estonia Finland France Germany Greece Hong Kong Hungary Iceland India (en) Indonesia (en) Ireland Israel (en) Italy Japan Korea Latvia Lithuania Malaysia (en) Mexico Netherlands New Zealand Norway Pakistan (en) Peru Philippines (en) Poland Portugal Romania Russia Saudi Arabia Singapore Slovakia Slovenia South Africa Spain (ca) Spain (es) Sweden Switzerland (de) Switzerland (fr) Taiwan Thailand (en) Turkey US (English) US (Spanish) Ukraine United Kingdom Vietnam (en) Any Time Past Day Past Week Past Month Past Year &nbsp; &nbsp;&nbsp;&nbsp;&nbsp; &nbsp; 1.&nbsp; Chicken Biryani ( Step-by-step Chicken Biryani) - Ruchiskitchen &nbsp;&nbsp;&nbsp; The traditional Chicken Biryani recipe appears intricate owing to the extensive list of ingredients and elaborate cooking techniques, which stops many from attempting it at home. But, I have tried to dispel that myth and simplified the process of making authentic biryani to help you create this culinary masterpiece with confidence. &nbsp;&nbsp;&nbsp; www.ruchiskitchen.com/chicken-biryani/ &nbsp; &nbsp; 2.&nbsp; Authentic Chicken Biryani Recipe Step by Step: Ultimate Flavor Guide &nbsp;&nbsp;&nbsp; This authentic chicken biryani recipe breaks down every step , making it easy for you to create a flavorful, aromatic dish at home. Imagine the rich spices, tender chicken, and fluffy rice coming together perfectly\\\\u2014right from your own kitchen. Keep reading, and you&#x27;ll discover simple tips that will turn your biryani into a family favorite. &nbsp;&nbsp;&nbsp; chickencooktemp.com/authentic-chicken-biryani-recipe-step-by-step/ &nbsp; &nbsp; 3.&nbsp; Easy Chicken Biryani (Shortcut Recipe) - Foodess &nbsp;&nbsp;&nbsp; How to Make Shortcut Chicken Biryani : An Easy Guide Simple steps , cozy and delicious payoff. It&#x27;s weeknight-friendly and big on flavor. (Try my life-changing butter chicken recipe , too!) Marinate the Chicken Toss chicken with lemon, garlic, garam masala, and salt. Set aside while you prep onions and rice. Quick marinating works here. &nbsp;&nbsp;&nbsp; foodess.com/easy-biryani-recipe/ &nbsp; &nbsp; 4.&nbsp; Chicken Biryani Recipe: Step-by-Step Cooking Instructions &nbsp;&nbsp;&nbsp; Learn an easy chicken biryani recipe with simple steps . Make a tasty Indian rice dish at home using spices and chicken, with a step-by-step guide. &nbsp;&nbsp;&nbsp; natures-spice.com/chicken-biryani-recipe-step-by-step-cooking/ &nbsp; &nbsp; 5.&nbsp; Easy Chicken Biryani Recipe - Step-by-Step Guide for Beginners &nbsp;&nbsp;&nbsp; Chicken Biryani is one of the most beloved dishes in Indian cuisine, known for its rich flavors, fragrant spices, and tender, juicy chicken pieces. Many home cooks feel intimidated by the process, but with the right steps , making chicken biryani at home can be straightforward and incredibly rewarding. This step-by-step guide will show you how to make an authentic chicken biryani that&#x27;s full ... &nbsp;&nbsp;&nbsp; recipibytes.com/indian-recipes/rice-recipes/easy-homemade-chicken-biryani-recipe-step-by-step-guide-for-beginners/ &nbsp; &nbsp; 6.&nbsp; Authentic Chicken Biryani Recipe | Step-by-Step Guide &nbsp;&nbsp;&nbsp; Authentic Chicken Biryani Recipe with basmati rice, tender chicken, and rich spices. Easy step-by-step method for perfect biryani every time. &nbsp;&nbsp;&nbsp; fahoria.com/authentic-chicken-biryani-recipe-perfect-flavor/ &nbsp; &nbsp; 7.&nbsp; Chicken Biryani | Indian One-Pot Rice And Chicken (Video) &nbsp;&nbsp;&nbsp; Learn how to make authentic chicken biryani at home with this step-by-step recipe using the traditional dum method. Includes tips, substitutions, and pro techniques for perfect results every time. &nbsp;&nbsp;&nbsp; www.pantsdownapronson.com/chicken-biryani-recipe/ &nbsp; &nbsp; 8.&nbsp; Chicken Bir\"}\"\"\"\ndata = $node_1_output$$\nprint('Biryani making process:')\nfor step in data:\n    print(step)"
}

def run(args):
    import io, contextlib, json as _json
    code = args.get("code", args.get("script", "")).strip()
    input_data = args.get("input", "")
    if not code:
        return "Error: no code provided in args"
    buf = io.StringIO()
    local_vars = {"INPUT": input_data, "json": _json}
    with contextlib.redirect_stdout(buf):
        exec(compile(code, "<amsab>", "exec"), local_vars)
    stdout = buf.getvalue().strip()
    output_var = local_vars.get("OUTPUT", "")
    result = stdout or str(output_var) if output_var else stdout
    return result if result else "(no output — add print() calls to your code)"

if __name__ == "__main__":
    try:
        result = run(ARGS)
        print(json.dumps({"status": "ok", "output": result}))
    except Exception as exc:
        print(json.dumps({"status": "error", "error": str(exc)}))
        sys.exit(1)
