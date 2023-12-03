from srbc.models import MealProduct, MealComponent


def calculate_component_protein(meal_component):
    product = meal_component.meal_product

    if product.has_tag('PROTEIN_SOURCE'):
        if product.component_type in [MealProduct.TYPE_UNKNOWN, MealProduct.TYPE_MIX]:
            if meal_component.has_custom_nutrition:
                # Белок учитываем только для продуктов, которые по нашей базе считаются носителями белка (БЭ > 0)
                if product.protein_proxy_percent > 0:
                    return (meal_component.details_protein or 0) * meal_component.weight / 100
                else:
                    return 0
            else:
                return (product.protein_proxy_percent or 0) * meal_component.weight / 100
        else:
            return (product.protein_proxy_percent or 0) * meal_component.weight / 100
    else:
        return 0


def calculate_meal_protein(meal):
    components = MealComponent.objects.filter(meal=meal).select_related('meal_product').all()

    total_protein = 0
    for component in components:
        total_protein += calculate_component_protein(component)

    return total_protein
