class Selenium:
    @staticmethod
    def get_src(element):
        return element["src"] if element else ""



    @staticmethod
    def get_text(element):
        return element.text if element else ""



    @staticmethod
    def get_content(element):
        return element["content"] if element else ""



    @staticmethod
    def get_selector_one_text(selector, dom):
        return dom.select_one(selector)



    @staticmethod
    def get_selector_text(selector, dom):
        return dom.select(selector)