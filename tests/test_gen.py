""" from utboxgen_py.generator import UTTextboxTemplate, generate_multi, Textbox

a = [
    Textbox.from_textbox(UTTextboxTemplate(scale=2),"Hopefully, this works."),
    Textbox.from_textbox(UTTextboxTemplate(), "I'm not sure what to put here..."),
    Textbox.from_textbox(UTTextboxTemplate(scale=2), "Проверка кириллицы."),
]

generate_multi(a, True).show() """
