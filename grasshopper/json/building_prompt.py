prompt = ""
size = ""
floors = ""


context = """You are an architect and you have to hand draw a simple building structure like boxy 'Seagram Building'
               with the provided info in prompt. Dont overcomplicate it because it is just the base.
               Just line draw the a simple boxy building"""
negative_context = "No environment, No extra Environment, No extra details,very simple building"
refined_prompt = f"context: {context}. \nnegative context(Remember this): {negative_context}.
    \nPrompt: {prompt} axiometric view, full view. \nFootprint of Building: {size} \nNumber of Floors: {floors} axiometric view, full view. "