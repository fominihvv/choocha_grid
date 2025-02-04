

class DataMixin:
    extra_context = {}
    paginate_by = 2

    @staticmethod
    def get_mixin_context(context: dict, **kwargs) -> dict:
        if "paginator" in context and "page_obj" in context:
            context["page_range"] = context["paginator"].get_elided_page_range(context["page_obj"].number,
                                                                               on_each_side=2, on_ends=1)
        context.update({**kwargs})
        return context
