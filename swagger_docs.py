from drf_yasg import openapi
from srbc.serializers.general import (
    BookmarkToggleSerializer, 
    MealFaultsSerializer, 
    MealProductSerializer, 
    DiaryMealDataAdminSerializer, 
    DiaryTodaySerializer,
    ParticipationGoalSerializer,
    ParticipationGoalStatusSerializer,
    UserShortSerializer,
    ProfileSerializer,
    DiaryRecordSerializer,
    InstagramImageSerializer,
    SRBCImageSerializer,
    UserProfileSerializer
)
from content.serializers import (
    TGChatSerializer,
    TGMessageSerializer,
    TGPostSerializer
    )
from srbc.serializers.task_based import CheckpointMeasurementSwaggerSerializer ,CheckpointMeasurementsSwaggerSerializer
from srbc.serializers.swagger import (
    CheckpointPhotoSwaggerSerializer, 
    MealFaultsByDateSwagger, 
    MealStatByDateSwagger, 
    AnalysisTemplateSwagger, 
    AnalysisAdminSerializer, 
    PutDiaryMealsSwaggerSerializer,
    PutMealsAdminSwaggerSerializer,
    AddPostTelegramSwagger
)
from srbc.serializers.task_based import (
    DiaryDataSerializer
    )
from content.serializers import ArticlesSerializer, ArticleSerializer, MeetingSerializer



swagger_docs = {

    'GET /v1/auth/apple/': {
        'tags': ['Auth'],
        'operation_summary': 'Аутентификация через Apple аккаунт',
        'operation_description': '',
        'manual_parameters': [openapi.Parameter('token', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True)],
        'responses': {
            200: openapi.Response('',
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'token': openapi.Schema(type=openapi.TYPE_STRING, description="JWT Токен"),
                    },
                )),
            403: openapi.Response('Forbidden', openapi.Schema(type=openapi.TYPE_STRING,))
            }, 
        },
    
    'GET /v1/auth/google/': {
        'tags': ['Auth'],
        'operation_summary': 'Аутентификация через Google аккаунт',
        'operation_description': '',
        'manual_parameters': [openapi.Parameter('token', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True)],
        'responses': {
            200: openapi.Response('',
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'token': openapi.Schema(type=openapi.TYPE_STRING, description="JWT Токен"),
                    },
                )),
            403: openapi.Response('Forbidden', openapi.Schema(type=openapi.TYPE_STRING,))
            }, 
        },

    'POST /v1/auth/refresh/': {
        'tags': ['Auth'],
        },

    'POST /v1/auth/credentials/': {
        'tags': ['Auth'],
        },
    
    'GET /v1/auth/facebook/': {
        'tags': ['Auth'],
        'operation_summary': 'Аутентификация через Facebook аккаунт',
        'operation_description': '',
        'manual_parameters': [openapi.Parameter('token', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True)],
        'responses': {
            200: openapi.Response('',
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'token': openapi.Schema(type=openapi.TYPE_STRING, description="JWT Токен"),
                    },
                )),
            403: openapi.Response('Forbidden', openapi.Schema(type=openapi.TYPE_STRING,))
            }, 
        },

    'GET /v1/auth/temporary/': {
        'tags': ['Auth'],
        'manual_parameters': [
            openapi.Parameter('token', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True),
            ],
        'operation_summary': 'Временная авторизация',
        'operation_description': 'Получение jwt токена, который действует 5 минут',
        'responses': {
            200: openapi.Response('',
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'token': openapi.Schema(type=openapi.TYPE_STRING, description="JWT Токен"),
                    },
                )),
            }, 
        },

    
    'GET /v1/analysis/{user_id}/regular/': {
        'tags': ['Staff analysis'],
        'manual_parameters': [
            openapi.Parameter('start_date', openapi.IN_QUERY, description='Формат `%Y-%m-%d`', type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
            openapi.Parameter('end_date', openapi.IN_QUERY, description='Формат `%Y-%m-%d`', type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
            ],
        'operation_summary': 'Анализ пользователя',
        'operation_description': 'Получение общей статистики пользователя за промежуток времени (по умолчанию за последние две недели)',
        'responses': {
            200: openapi.Response('',
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'faults_stat': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Items(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        'code': openapi.Schema(type=openapi.TYPE_STRING),
                                        'count': openapi.Schema(type=openapi.TYPE_INTEGER),
                                        'days': openapi.Schema(type=openapi.TYPE_INTEGER),
                                        'fault': openapi.Schema(
                                                    type=openapi.TYPE_OBJECT,
                                                    properties={
                                                        'comment': openapi.Schema(type=openapi.TYPE_STRING),
                                                        'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                                        'scopes': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
                                                        'title': openapi.Schema(type=openapi.TYPE_STRING),
                                                    }
                                                ),
                                        'stat': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_INTEGER)),
                                    }
                                )
                            ),
                        'balance_stat': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Items(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        'code': openapi.Schema(type=openapi.TYPE_STRING),
                                        'count': openapi.Schema(type=openapi.TYPE_INTEGER),
                                        'days': openapi.Schema(type=openapi.TYPE_INTEGER),
                                        'fault': openapi.Schema(
                                                    type=openapi.TYPE_OBJECT,
                                                    properties={
                                                        'comment': openapi.Schema(type=openapi.TYPE_STRING),
                                                        'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                                        'scopes': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
                                                        'title': openapi.Schema(type=openapi.TYPE_STRING),
                                                    }
                                                ),
                                        'stat': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_INTEGER)),
                                    }
                                )
                            ),
                        'opp_stat': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Items(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        'code': openapi.Schema(type=openapi.TYPE_STRING),
                                        'count': openapi.Schema(type=openapi.TYPE_INTEGER),
                                        'days': openapi.Schema(type=openapi.TYPE_INTEGER),
                                        'fault': openapi.Schema(
                                                    type=openapi.TYPE_OBJECT,
                                                    properties={
                                                        'comment': openapi.Schema(type=openapi.TYPE_STRING),
                                                        'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                                        'scopes': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
                                                        'title': openapi.Schema(type=openapi.TYPE_STRING),
                                                    }
                                                ),
                                        'stat': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_INTEGER)),
                                    }
                                )
                            ),
                        'product_tags_stat': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Items(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        'code': openapi.Schema(type=openapi.TYPE_STRING),
                                        'count': openapi.Schema(type=openapi.TYPE_INTEGER),
                                        'days': openapi.Schema(type=openapi.TYPE_INTEGER),
                                        'weight': openapi.Schema(type=openapi.TYPE_INTEGER),
                                        'title': openapi.Schema(type=openapi.TYPE_STRING),
                                        'stat': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_INTEGER)),
                                    }
                                )
                            ),
                        'comp_stat': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Items(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        'code': openapi.Schema(type=openapi.TYPE_STRING),
                                        'count': openapi.Schema(type=openapi.TYPE_INTEGER),
                                        'days': openapi.Schema(type=openapi.TYPE_INTEGER),
                                        'weight': openapi.Schema(type=openapi.TYPE_INTEGER),
                                        'title': openapi.Schema(type=openapi.TYPE_STRING),
                                        'stat': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_INTEGER)),
                                    }
                                )
                            ),
                        'fatcarb_list': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Items(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'meal_product__id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'product_title': openapi.Schema(type=openapi.TYPE_STRING),
                                    'total': openapi.Schema(type=openapi.TYPE_INTEGER),
                                }
                                )
                        ),
                        'water_stat': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Items(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'date': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
                                    'water_flag': openapi.Schema(type=openapi.TYPE_STRING),
                                    'water': openapi.Schema(type=openapi.TYPE_NUMBER),
                                    'water_per_kilo': openapi.Schema(type=openapi.TYPE_NUMBER),
                                    'water_percentage': openapi.Schema(type=openapi.TYPE_NUMBER),
                                }
                            )
                        ),
                        'water_stat_summary': openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'avg': openapi.Schema(type=openapi.TYPE_NUMBER),
                                    'dry_days_avg': openapi.Schema(type=openapi.TYPE_NUMBER),
                                    'dry_days_count': openapi.Schema(type=openapi.TYPE_NUMBER),
                                    'filled_days': openapi.Schema(type=openapi.TYPE_NUMBER),
                                    'norm_days': openapi.Schema(type=openapi.TYPE_NUMBER),
                                }
                        ),
                        'hunger_stat': openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'days': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'hunger_total': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'stat': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_STRING)),
                                }
                        ),
                        'dates': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Items(
                                type=openapi.TYPE_STRING,
                                format=openapi.FORMAT_DATE
                            )
                        ),
                        'meal_dates': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Items(
                                type=openapi.TYPE_STRING,
                                format=openapi.FORMAT_DATE
                            )
                        ),
                        'meal_class_days':  openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Items(
                                type=openapi.TYPE_STRING,
                            )
                        ),
                        "last_note": openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'add_fat': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                    'adjust_calories': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                    'adjust_carb_bread_late': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                    'adjust_carb_bread_min': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                    'adjust_carb_carb_vegs': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                    'adjust_carb_mix_vegs': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                    'adjust_carb_sub_breakfast': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                    'adjust_fruits': openapi.Schema(type=openapi.TYPE_STRING),
                                    'adjust_protein': openapi.Schema(type=openapi.TYPE_NUMBER),
                                    'author': openapi.Schema(type=openapi.TYPE_STRING),
                                    'content': openapi.Schema(type=openapi.TYPE_STRING),
                                    'date_added': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                                    'exclude_lactose': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                    'get_adjust_fruits_display': openapi.Schema(type=openapi.TYPE_STRING),
                                    'has_meal_adjustments': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                    'is_published': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                    'restrict_lactose_casein': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                }
                        ),
                        "doc_notes": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Items(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'add_fat': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                    'adjust_calories': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                    'adjust_carb_bread_late': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                    'adjust_carb_bread_min': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                    'adjust_carb_carb_vegs': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                    'adjust_carb_mix_vegs': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                    'adjust_carb_sub_breakfast': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                    'adjust_fruits': openapi.Schema(type=openapi.TYPE_STRING),
                                    'adjust_protein': openapi.Schema(type=openapi.TYPE_NUMBER),
                                    'author': openapi.Schema(type=openapi.TYPE_STRING),
                                    'content': openapi.Schema(type=openapi.TYPE_STRING),
                                    'date_added': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                                    'exclude_lactose': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                    'get_adjust_fruits_display': openapi.Schema(type=openapi.TYPE_STRING),
                                    'has_meal_adjustments': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                    'is_published': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                    'restrict_lactose_casein': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                }
                            )
                        ),
                        "steps_stat": openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'active_days': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'filled_days': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'lazy_days': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'lazy_days_avg_percent': openapi.Schema(type=openapi.TYPE_NUMBER),
                                    
                                }
                        ),
                        'meal_stat': openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'fault_days': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'fault_days_meals_avg': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'faults_sum': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'faulty_days_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'ok_days': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'filled_days': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'ok_days_percent': openapi.Schema(type=openapi.TYPE_NUMBER),
                                }
                        ),
                        'weight_stat': openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'trueweight_delta_interval': openapi.Schema(type=openapi.TYPE_NUMBER),
                                    'trueweight_delta_weekly': openapi.Schema(type=openapi.TYPE_NUMBER),
                                    'prev_trueweight_delta_interval': openapi.Schema(type=openapi.TYPE_NUMBER),
                                    'prev_trueweight_delta_weekly': openapi.Schema(type=openapi.TYPE_NUMBER),
                                }
                        ),
                        'pers_req': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Items(
                                type=openapi.TYPE_STRING
                            )
                            ),
                        'pers_req_stat': openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'general': openapi.Schema(
                                            type=openapi.TYPE_OBJECT,
                                            properties={
                                                'days': openapi.Schema(type=openapi.TYPE_INTEGER),
                                                'success_days': openapi.Schema(type=openapi.TYPE_INTEGER),
                                            }
                                    ),
                                    'recommendations': openapi.Schema(
                                            type=openapi.TYPE_OBJECT,
                                            properties={
                                                'code': openapi.Schema(type=openapi.TYPE_STRING),
                                                'title': openapi.Schema(type=openapi.TYPE_STRING),
                                                'stat': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_INTEGER)),
                                            }
                                    ),
                                }
                        ),
                    },
                )),
            }, 
        },

    'PUT /v1/bookmarks/': {
        'request_body': BookmarkToggleSerializer,
        'tags': ['Bookmarks'],
        'operation_summary': 'Добавление пользователя в закладки',
        'responses': {
            200: openapi.Response(
            'OK', 
            openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'status': openapi.Schema(type=openapi.TYPE_STRING, enum=["added","removed"])
                }
            )
            
        )
        }
    },

    'PATCH /v1/bookmarks/': {
        'request_body': BookmarkToggleSerializer,
        'tags': ['Bookmarks'],
        'operation_summary': 'Обновление закладки',
        'responses': {
            200: openapi.Response(
            'OK', 
            openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'status': openapi.Schema(type=openapi.TYPE_STRING, enum=["added","removed"])
                }
            )
            
        )
        }
    },

    'HEAD /v1/chat/{chat_id}/notify/': {
        'tags': ['Telegram channel administration'],
        'operation_summary': 'Уведомление пользователя для присоединения к чату',
        'operation_description': '',
        'responses': {
            200: openapi.Response(
            '', 
            openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'result': openapi.Schema(type=openapi.TYPE_STRING, enum=["ok", "not_found"])
                }
                ))
            }
        },
    
    'GET /v1/checkpoints/measurements/': {
        'tags': ['Checkpoints'],
        'operation_summary': 'Получение данных по всем замерам пользователя ',
        'operation_description': '',
        'responses': {
            200: openapi.Response(
                'Данные всех чекпоинтов пользователя ', 
                CheckpointMeasurementsSwaggerSerializer
                ),
            403: 'Не хватает прав на выполнение запроса',
            }

    },

    'GET /v1/checkpoints/{user_id}/measurements/': {
        'tags': ['Admin checkpoints'],
        'operation_summary': 'Получение данных по всем замерам пользователя ',
        'operation_description': '',
        'responses': {
            200: openapi.Response(
                'Данные всех чекпоинтов пользователя ', 
                CheckpointMeasurementsSwaggerSerializer
                ),
            403: 'Не хватает прав на выполнение запроса',
            }

    },

    'GET /v1/checkpoints/measurements/{date}/': {
        'tags': ['Checkpoints'],
        'operation_summary': 'Получение данных чекпоинта за указанную дату ',
        'manual_parameters': [openapi.Parameter('date', openapi.IN_PATH, type=openapi.TYPE_STRING, required=True, format=openapi.FORMAT_DATE, description='Формат `%Y-%m-%d`')],
        'operation_description': '',
        'responses': {
            200: openapi.Response(
                'Данные чекпоинта за указанную дату', 
                CheckpointMeasurementSwaggerSerializer
                ),
            403: 'Не хватает прав на выполнение запроса',
            404: 'Нет чекпоинта за указанную дату',
            400: 'Неверный формат даты в запросе'
            }
    },

    'POST /v1/checkpoints/measurements/{date}/': {
        'tags': ['Checkpoints'],
        'operation_summary': 'Создать чекпоинт за определенную дату',
        'manual_parameters': [openapi.Parameter('date', openapi.IN_PATH, type=openapi.TYPE_STRING, required=True, format=openapi.FORMAT_DATE, description='Формат `%Y-%m-%d`')],
        'operation_description': '',
        'responses': {
            200: openapi.Response(
                'Данные созданного чекпоинта', 
                CheckpointMeasurementSwaggerSerializer
                ),
            403: 'Не хватает прав на выполнение запроса',
            409: 'Чекпоинт за запрошенную дату уже существует',
            400: 'Неверный формат даты в запросе'
            }
    },

    'PATCH /v1/checkpoints/measurements/{date}/': {
        'tags': ['Checkpoints'],
        'request_body': CheckpointMeasurementSwaggerSerializer,
        'operation_summary': 'Изменяет данные РЕДАКТИРУЕМОГО чекпоинта',
        'manual_parameters': [openapi.Parameter('date', openapi.IN_PATH, type=openapi.TYPE_STRING, required=True, format=openapi.FORMAT_DATE, description='Формат `%Y-%m-%d`')],
        'operation_description': '',
        'responses': {
            200: openapi.Response(
                'Данные созданного чекпоинта', 
                CheckpointMeasurementSwaggerSerializer
                ),
            403: 'Не хватает прав на выполнение запроса',
            409: 'Дата, на которую изменяем чекпоинт, уже занята другим чекпоинтом',
            400: 'Неверный формат даты в запросе',
            404: 'Не найден редактируемый чекпоинт за указанную дату'
            }
    },

    'DELETE /v1/checkpoints/measurements/{date}/': {
        'tags': ['Checkpoints'],
        'operation_summary': 'Удалить замер за определенную дату (если он редактируем и is_measurements_done=False)',
        'manual_parameters': [openapi.Parameter('date', openapi.IN_PATH, type=openapi.TYPE_STRING, required=True, format=openapi.FORMAT_DATE, description='Формат `%Y-%m-%d`')],
        'operation_description': '',
        'responses': {
            204: 'Чекпоинт за переданную дату успешно удален',
            403: 'Не хватает прав на выполнение запроса',
            400: 'Неверный формат даты в запросе',
            404: 'Не найден редактируемый чекпоинт c is_measurements_done=False за указанную дату'
            }
    },

    'GET /v1/checkpoints/{user_id}/measurements/{date}/': {
        'tags': ['Admin checkpoints'],
        'operation_summary': 'Получение данных чекпоинта за указанную дату ',
        'manual_parameters': [openapi.Parameter('date', openapi.IN_PATH, type=openapi.TYPE_STRING, required=True, format=openapi.FORMAT_DATE, description='Формат `%Y-%m-%d`')],
        'operation_description': '',
        'responses': {
            200: openapi.Response(
                'Данные чекпоинта за указанную дату', 
                CheckpointMeasurementSwaggerSerializer
                ),
            403: 'Не хватает прав на выполнение запроса',
            404: 'Нет чекпоинта за указанную дату',
            400: 'Неверный формат даты в запросе'
            }
    },

    'POST /v1/checkpoints/{user_id}/measurements/{date}/': {
        'tags': ['Admin checkpoints'],
        'operation_summary': 'Создать чекпоинт за определенную дату',
        'manual_parameters': [openapi.Parameter('date', openapi.IN_PATH, type=openapi.TYPE_STRING, required=True, format=openapi.FORMAT_DATE, description='Формат `%Y-%m-%d`')],
        'operation_description': '',
        'responses': {
            200: openapi.Response(
                'Данные созданного чекпоинта', 
                CheckpointMeasurementSwaggerSerializer
                ),
            403: 'Не хватает прав на выполнение запроса',
            409: 'Чекпоинт за запрошенную дату уже существует',
            400: 'Неверный формат даты в запросе'
            }
    },

    'PATCH /v1/checkpoints/{user_id}/measurements/{date}/': {
        'tags': ['Admin checkpoints'],
        'request_body': CheckpointMeasurementSwaggerSerializer,
        'operation_summary': 'Изменяет данные РЕДАКТИРУЕМОГО чекпоинта',
        'manual_parameters': [openapi.Parameter('date', openapi.IN_PATH, type=openapi.TYPE_STRING, required=True, format=openapi.FORMAT_DATE, description='Формат `%Y-%m-%d`')],
        'operation_description': '',
        'responses': {
            200: openapi.Response(
                'Данные созданного чекпоинта', 
                CheckpointMeasurementSwaggerSerializer
                ),
            403: 'Не хватает прав на выполнение запроса',
            409: 'Дата, на которую изменяем чекпоинт, уже занята другим чекпоинтом',
            400: 'Неверный формат даты в запросе',
            404: 'Не найден редактируемый чекпоинт за указанную дату'
            }
    },

    'DELETE /v1/checkpoints/{user_id}/measurements/{date}/': {
        'tags': ['Admin checkpoints'],
        'operation_summary': 'Удалить замер за определенную дату (если он редактируем и is_measurements_done=False)',
        'manual_parameters': [openapi.Parameter('date', openapi.IN_PATH, type=openapi.TYPE_STRING, required=True, format=openapi.FORMAT_DATE, description='Формат `%Y-%m-%d`')],
        'operation_description': '',
        'responses': {
            204: 'Чекпоинт за переданную дату успешно удален',
            403: 'Не хватает прав на выполнение запроса',
            400: 'Неверный формат даты в запросе',
            404: 'Не найден редактируемый чекпоинт c is_measurements_done=False за указанную дату'
            }
    },
    
    'GET /v1/checkpoints/photos/': {
        'tags': ['Checkpoints'],
        'operation_summary': 'Получение всех контрольных фото',
        'operation_description': '',
        'responses': {
            404: 'Не хватает прав на выполнение запроса',
            200: openapi.Response(
                'OK',
                CheckpointPhotoSwaggerSerializer(many=True)
            )
            }
    },

    'GET /v1/checkpoints/{user_id}/photos/': {
        'tags': ['Admin checkpoints'],
        'operation_summary': 'Получение всех контрольных фото',
        'operation_description': '',
        'responses': {
            404: 'Не хватает прав на выполнение запроса',
            200: openapi.Response(
                'OK',
                CheckpointPhotoSwaggerSerializer(many=True)
            )
            }
    },

    'PUT /v1/checkpoints/photos/': {
        'tags': ['Checkpoints'],
        'operation_summary': 'Сделать коллаж',
        'request_body': openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['id'],
            properties={
                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
            }
        ),
        'operation_description': '',
        'responses': {
            404: 'Фотосет не найден',
            200: openapi.Response(
                'OK',
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'task_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                    }
                ),
            )
            }
    },

    'PUT /v1/checkpoints/{user_id}/photos/': {
        'tags': ['Admin checkpoints'],
        'operation_summary': 'Сделать коллаж',
        'request_body': openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['id'],
            properties={
                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
            }
        ),
        'operation_description': '',
        'responses': {
            404: 'Фотосет не найден',
            200: openapi.Response(
                'OK',
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'task_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                    }
                ),
            )
            }
    },

    'PATCH /v1/checkpoints/photos/': {
        'tags': ['Checkpoints'],
        'operation_summary': 'Обрезать фотографии',
        'request_body': openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['id', 'crop_meta'],
            properties={
                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'crop_meta': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'font': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'crop': openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        'top': openapi.Schema(type=openapi.TYPE_INTEGER),
                                        'left': openapi.Schema(type=openapi.TYPE_INTEGER),
                                        'width': openapi.Schema(type=openapi.TYPE_INTEGER),
                                        'height': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    }
                                ),
                                'angle': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'eyeline': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'kneeline': openapi.Schema(type=openapi.TYPE_INTEGER),
                            }
                        ),
                        'rear': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'crop': openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        'top': openapi.Schema(type=openapi.TYPE_INTEGER),
                                        'left': openapi.Schema(type=openapi.TYPE_INTEGER),
                                        'width': openapi.Schema(type=openapi.TYPE_INTEGER),
                                        'height': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    }
                                ),
                                'angle': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'eyeline': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'kneeline': openapi.Schema(type=openapi.TYPE_INTEGER),
                            }
                        ),
                        'side': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'crop': openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        'top': openapi.Schema(type=openapi.TYPE_INTEGER),
                                        'left': openapi.Schema(type=openapi.TYPE_INTEGER),
                                        'width': openapi.Schema(type=openapi.TYPE_INTEGER),
                                        'height': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    }
                                ),
                                'angle': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'eyeline': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'kneeline': openapi.Schema(type=openapi.TYPE_INTEGER),
                            }
                        )
                    }
                )
            }
        ),
        'operation_description': '',
        'responses': {
            404: 'Фотосет не найден',
            200: openapi.Response(
                'OK',
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'task_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                    }
                ),
            )
            }
    },

    'PATCH /v1/checkpoints/{user_id}/photos/': {
        'tags': ['Admin checkpoints'],
        'operation_summary': 'Обрезать фотографии',
        'request_body': openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['id', 'crop_meta'],
            properties={
                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'crop_meta': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'font': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'crop': openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        'top': openapi.Schema(type=openapi.TYPE_INTEGER),
                                        'left': openapi.Schema(type=openapi.TYPE_INTEGER),
                                        'width': openapi.Schema(type=openapi.TYPE_INTEGER),
                                        'height': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    }
                                ),
                                'angle': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'eyeline': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'kneeline': openapi.Schema(type=openapi.TYPE_INTEGER),
                            }
                        ),
                        'rear': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'crop': openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        'top': openapi.Schema(type=openapi.TYPE_INTEGER),
                                        'left': openapi.Schema(type=openapi.TYPE_INTEGER),
                                        'width': openapi.Schema(type=openapi.TYPE_INTEGER),
                                        'height': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    }
                                ),
                                'angle': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'eyeline': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'kneeline': openapi.Schema(type=openapi.TYPE_INTEGER),
                            }
                        ),
                        'side': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'crop': openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        'top': openapi.Schema(type=openapi.TYPE_INTEGER),
                                        'left': openapi.Schema(type=openapi.TYPE_INTEGER),
                                        'width': openapi.Schema(type=openapi.TYPE_INTEGER),
                                        'height': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    }
                                ),
                                'angle': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'eyeline': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'kneeline': openapi.Schema(type=openapi.TYPE_INTEGER),
                            }
                        )
                    }
                )
            }
        ),
        'operation_description': '',
        'responses': {
            404: 'Фотосет не найден',
            200: openapi.Response(
                'OK',
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'task_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                    }
                ),
            )
            }
    },


    'GET /v1/content/articles/': {
        'tags': ['Articles'],
        'operation_summary': 'Выводит список статей, доступных пользователю.',
        'operation_description': '',
        'responses': {
            200: openapi.Response(
                'Список статей',
                ArticlesSerializer(many=True)
            )
            }
    },

    'GET /v1/content/articles/{article_id}/': {
        'tags': ['Articles'],
        'operation_summary': 'Выводит фото, видео, текст статьи, если эта статья доступна пользователю',
        'operation_description': '',
        'responses': {
            200: openapi.Response(
                'Данные статьи',
                ArticleSerializer
            ),
            404: 'Запрашиваемая статья не найдена или нет доступа к ней'
            }
    },

    'GET /v1/content/meetings/': {
        'tags': ['Meetings​'],
        'operation_summary': 'Выводит список лекций',
        'operation_description': '',
        'responses': {
            200: openapi.Response(
                'Список лекций',
                MeetingSerializer(many=True)
            ),
            }
    },

    'GET /v1/user/{user_id}/diaries/{diary_date}/meal_review/': {
        'tags': ['Staff analysis'],
        'operation_summary': 'Получение списка действий по накоплению жира в выбранном рационе у выбранного пользователя',
        'operation_description': '',
        'responses': {
            200: openapi.Response(
                'OK',
                MealFaultsByDateSwagger
            ),
            404: 'Рацион за эту дату не найден'
            }
    },

    'GET /v1/user/{user_id}/diaries/{diary_date}/meal_stat/': {
        'tags': ['Staff analysis'],
        'operation_summary': 'Получение анализа рациона пользователя',
        'operation_description': '',
        'responses': {
            200: openapi.Response(
                'OK',
                MealStatByDateSwagger
            ),
            404: 'Рацион за эту дату не найден'
            }
    },

    'GET /v1/profile/{user_id}/analysis/templates/': {
        'tags': ['Staff analysis'],
        'operation_summary': 'Получение анализа рациона пользователя',
        'operation_description': '',
        'responses': {
            200: openapi.Response(
                'OK',
                AnalysisTemplateSwagger
            ),
            }
    },

    'POST /v1/profile/{user_id}/analysis/add/': {
        'tags': ['Staff analysis'],
        'operation_summary': 'Добавление персональной рекомендации',
        'operation_description': '',
        'request_body': AnalysisAdminSerializer,
        'responses': {
            200: openapi.Response(
                'OK',
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'user_note': openapi.Schema(type=openapi.TYPE_INTEGER)
                    }
                )
            ),
            400: 'Данные не корректны',
            404: 'Пользователь не найден',
            }
    },

    'GET /v1/diary/faults/': {
        'tags': ['Diary'],
        'operation_summary': 'Получение общей статистики действий по накоплению жира у текущего пользователя',
        'operation_description': '',
        'responses': {
            200: openapi.Response(
                'OK',
                MealFaultsSerializer(many=True)
            ),
            }
    },

    'GET /v1/diary/not-ready/{diary_date}/': {
        'tags': ['Diary'],
        'operation_summary': 'Получение записей в дневнике со статусом "Ожидает заполнения"',
        'operation_description': '',
        'responses': {
            200: openapi.Response(
                'OK',
                openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE)
                )
            ),
            }
    },

    'GET /v1/diary/products/': {
        'tags': ['Diary'],
        'operation_summary': 'Получение списка имеющихся продуктов',
        'operation_description': '',
        'manual_parameters': [openapi.Parameter('q', openapi.IN_QUERY, type=openapi.TYPE_STRING)],
        'responses': {
            200: openapi.Response(
                'OK',
                MealProductSerializer(many=True)
            ),
            }
    },

    'GET /v1/diary/products/wiki/': {
        'tags': ['Diary'],
        'operation_summary': 'Получение продукта страницы продукта на Википедии',
        'operation_description': '(или если он имеется в списке продуктов то выводит имеющийся продукт)',
        'manual_parameters': [openapi.Parameter('q', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True)],
        'responses': {
            200: openapi.Response(
                'OK',
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'url': openapi.Schema(type=openapi.TYPE_STRING),
                        'title': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            400: 'Bad request'
            }
    },

    'GET /v1/diary/{diary_date}/meals/': {
        'tags': ['Diary'],
        'operation_summary': 'Получение данных о рационе',
        'operation_description': '',
        'manual_parameters': [
            openapi.Parameter('diary_date', openapi.IN_PATH, description='Формат `%Y-%m-%d`', type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
            ],
        'responses': {
            200: openapi.Response(
                'OK',
                DiaryMealDataAdminSerializer
            ),
        }
    },

    'GET /v1/diary/{diary_user}/{diary_date}/meals/': {
        'tags': ['Admin diary'],
        'operation_summary': 'Получение данных о рационе',
        'operation_description': '',
        'manual_parameters': [
            openapi.Parameter('diary_date', openapi.IN_PATH, description='Формат `%Y-%m-%d`', type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
            ],
        'responses': {
            200: openapi.Response(
                'OK',
                DiaryMealDataAdminSerializer
            ),
        }
    },

    'PUT /v1/diary/{diary_date}/meals/': {
        'tags': ['Diary'],
        'request_body': PutDiaryMealsSwaggerSerializer,
        'operation_summary': 'Обновление/Создание записи рациона',
        'manual_parameters': [
            openapi.Parameter('diary_date', openapi.IN_PATH, description='Формат `%Y-%m-%d`', type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
            ],
        'responses': {
            200: openapi.Response(
                'OK',
                DiaryMealDataAdminSerializer
            ),
            400: 'Bad request'
        }
    },

    'PUT /v1/diary/{diary_user}/{diary_date}/meals/': {
            'tags': ['Admin diary'],
            'request_body': PutMealsAdminSwaggerSerializer,
            'operation_summary': 'Сохранение данных анализа рациона',
            'manual_parameters': [
                openapi.Parameter('diary_date', openapi.IN_PATH, description='Формат `%Y-%m-%d`', type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
                ],
            'responses': {
                200: openapi.Response(
                    'OK',
                    DiaryMealDataAdminSerializer
                ),
                400: 'Bad request'
            }
        },

    'PATCH /v1/diary/{diary_user}/{diary_date}/data/': {
            'tags': ['Admin diary'],
            'request_body': openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'weight': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                    'steps':  openapi.Schema(type=openapi.TYPE_INTEGER),
                    'sleep':  openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                }
            ),
            'operation_summary': 'Обновление данных пользователя из админки. Только Шаги, Сон и Вес',
            'manual_parameters': [
                openapi.Parameter('diary_date', openapi.IN_PATH, description='Формат `%Y-%m-%d`', type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
                ],
            'responses': {
                200: openapi.Response(
                    'OK',
                    DiaryDataSerializer
                ),
                400: 'Bad request',
                403: 'No access to user data',
                409: 'Data for the date is readonly'
            }
        },
    
    'PUT /v1/diary/{diary_date}/meals/image/{meal_dt}/': {
            'tags': ['Diary'],
            'request_body': openapi.Schema(
                type=openapi.TYPE_OBJECT,
                required=['meal_image'],
                properties={
                    'meal_image': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_BASE64, description='base64'),
                }
            ),
            'operation_summary': 'Сохранение на сервер фото приема пищи',
            'manual_parameters': [
                openapi.Parameter('diary_date', openapi.IN_PATH, description='Формат `%Y-%m-%d`', type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
                openapi.Parameter('meal_dt', openapi.IN_PATH, description='Формат `%Y-%m-%d_%H:%M:%S`', type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                ],
            'responses': {
                200: openapi.Response(
                    'OK',
                    DiaryDataSerializer
                ),
                400: 'Bad request',
            }
        },

    'PUT /v1/images/meals/': {
            'tags': ['Meals'],
            'request_body': openapi.Schema(
                type=openapi.TYPE_OBJECT,
                required=['image','date'],
                properties={
                    'image': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_BASE64, description='base64'),
                    'date': openapi.Schema(type=openapi.TYPE_STRING, description='Формат `%Y-%m-%d`', format=openapi.FORMAT_DATE),
                }
            ),
            'operation_summary': 'Сохранение на сервер коллажа рациона',
            'responses': {
                200: 'OK',
                400: 'Bad request',
            }
        },

    
    'DELETE /v1/diary/{diary_date}/meals/image/{meal_dt}/': {
            'tags': ['Diary'],
            'operation_summary': 'Удаление фото приема пищи',
            'manual_parameters': [
                openapi.Parameter('diary_date', openapi.IN_PATH, description='Формат `%Y-%m-%d`', type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
                openapi.Parameter('meal_dt', openapi.IN_PATH, description='Формат `%Y-%m-%d_%H:%M:%S`', type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                ],
            'responses': {
                200: openapi.Response(
                    'OK',
                    DiaryMealDataAdminSerializer
                ),
                400: 'Bad request',
                404: "Not found"
            }
        },

    'GET /v1/diary/{diary_user}/{diary_date}/': {
            'tags': ['Admin diary'],
            'operation_summary': 'Получение данных дневника за выбранную дату',
            'manual_parameters': [
                openapi.Parameter('diary_date', openapi.IN_PATH, description='Формат `%Y-%m-%d`', type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
                openapi.Parameter('diary_user', openapi.IN_PATH, type=openapi.TYPE_INTEGER),
                ],
            'responses': {
                200: openapi.Response(
                    'OK',
                    DiaryTodaySerializer
                ),
                400: 'Bad request',
                404: "Not found"
            }
        },

    'GET /v1/diary/{user_id}/stat/meals/': {
            'tags': ['Admin diary'],
            'operation_summary': 'Получение общей статистики действий по накоплению жира у выбранного пользователя',
            'manual_parameters': [
                openapi.Parameter('start', openapi.IN_QUERY, description='Формат `%Y-%m-%d`', type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
                openapi.Parameter('end', openapi.IN_QUERY, description='Формат `%Y-%m-%d`', type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
                ],
            'responses': {
                200: openapi.Response(
                    'OK',
                    openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(type=openapi.TYPE_INTEGER)
                    )
                ),
                404: "Not found"
            }
        },

    'GET /v1/diary/{user_id}/stat/report/': {
            'tags': ['Admin diary'],
            'operation_summary': 'Сгенерировать для пользователя PDF-отчет со статистикой участия',
            'responses': {
                200: openapi.Response(
                    'OK',
                    openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'hashid': openapi.Schema(type=openapi.TYPE_STRING)
                        }
                    )
                ),
            }
        },
    
    'GET /v1/diary/stat/report/': {
            'tags': ['Diary'],
            'operation_summary': 'Сгенерировать для пользователя PDF-отчет со статистикой участия',
            'responses': {
                200: openapi.Response(
                    'OK',
                    openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'hashid': openapi.Schema(type=openapi.TYPE_STRING)
                        }
                    )
                ),
            }
        },

    'GET /v1/diary/{user_id}/stat/user/': {
            'tags': ['Admin diary'],
            'operation_summary': 'Получить общую статистику участия пользователя за период (по умолчанию - с 01.01.1970 по настоящий момент)',
            'operation_id': 'api_v3_profiles_usernote_list',
            'manual_parameters': [
                openapi.Parameter('start', openapi.IN_QUERY, description='Кол-во миллисекунд от 01.01.1970 00:00:00', type=openapi.TYPE_INTEGER),
                openapi.Parameter('end', openapi.IN_QUERY, description='Кол-во миллисекунд от 01.01.1970 00:00:00', type=openapi.TYPE_INTEGER),
                ],
            'responses': {
                200: openapi.Response(
                    'OK',
                    openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                        "weight_init": openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                        "trueweight_init": openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                        "weight_last": openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                        "weight_date_last": openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                        "trueweight_last": openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                        "faults_sum": openapi.Schema(type=openapi.TYPE_INTEGER),
                        "faulty_days_count": openapi.Schema(type=openapi.TYPE_INTEGER),
                        "pers_rec_ok_days_count": openapi.Schema(type=openapi.TYPE_INTEGER),
                        "pers_rec_total_days_count": openapi.Schema(type=openapi.TYPE_INTEGER),
                        "meal_days_total": openapi.Schema(type=openapi.TYPE_INTEGER),
                        "steps_sum": openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                        "steps_achieved_days_count": openapi.Schema(type=openapi.TYPE_INTEGER),
                        "steps_days_total": openapi.Schema(type=openapi.TYPE_INTEGER),
                        "sleep_sum": openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                        "sleep_achieved_days_count": openapi.Schema(type=openapi.TYPE_INTEGER),
                        "sleep_days_total": openapi.Schema(type=openapi.TYPE_INTEGER),
                        "weight_delta_start": openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                        "trueweight_delta_start": openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                        "trueweight_percent_start": openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                        "weeks_count": openapi.Schema(type=openapi.TYPE_INTEGER),
                        "trueweight_delta_weekly": openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_FLOAT),
                        "weight_delta_interval": openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                        "trueweight_delta_interval": openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                        "steps_avg_interval": openapi.Schema(type=openapi.TYPE_STRING, description='percentage'),
                        "sleep_avg_interval": openapi.Schema(type=openapi.TYPE_STRING, description='percentage'),
                    }
                    )
                ),
            }
        },

        'GET /v1/goals/': {
            'tags': ['Goals'],
            'operation_summary': 'Получения списка целей пользователя',
            'responses': {
                200: openapi.Response(
                    'OK',
                    ParticipationGoalSerializer(many=True)
                ),
            }
        },
        
        'POST /v1/goals/':{
            'tags': ['Goals'],
            'operation_summary': 'Добавить цель',
            'operation_description': '',
            'request_body': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        required=['title','text'],
                        properties={
                            "title": openapi.Schema(type=openapi.TYPE_STRING),
                            "text": openapi.Schema(type=openapi.TYPE_STRING),
                        }
                    ),
            'responses': {
                200: openapi.Response(
                    'OK',
                    ParticipationGoalSerializer
                ),
                400: 'Bad request'
            }
        },

        'PATCH /v1/goals/{goal_id}/':{
            'tags': ['Goals'],
            'operation_summary': 'Редактирование недостигнутой цели',
            'operation_description': 'Редактирование недостигнутой цели.\n\
                            Если мы хотим изменить цель – старую помечаем как "неактуальная" (флаг "удаленная"),\n\
                            и создается новая цель. Данная логика работает при любом изменении.',
            'request_body': ParticipationGoalStatusSerializer,
            'responses': {
                200: openapi.Response(
                    'OK',
                    ParticipationGoalSerializer
                ),
                400: 'Bad request',
                404: 'Not found'
            }
        },

        'GET /v1/meals/recommendations/':{
            'tags': ['Meals'],
            'operation_summary': 'Список персонализированных рекомендаций',
            'operation_description': 'На основании рекомендаций (UserNote) составляет рекомендации по приему пищи для пользователя.',
            'manual_parameters': [
                openapi.Parameter('date', openapi.IN_PATH, description='Формат `%Y-%m-%d`', type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
                ],
            'responses': {
                200: openapi.Response(
                    'OK',
                    openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "BREAKFAST": openapi.Schema(
                                    type=openapi.TYPE_ARRAY,
                                    items=openapi.Schema(
                                        type=openapi.TYPE_ARRAY,
                                        items=openapi.Schema(
                                            type=openapi.TYPE_OBJECT,
                                            properties={
                                                "component_type": openapi.Schema(type=openapi.TYPE_STRING),
                                                "weight_min": openapi.Schema(type=openapi.TYPE_INTEGER),
                                                "weight_max": openapi.Schema(type=openapi.TYPE_INTEGER),
                                                "weight": openapi.Schema(type=openapi.TYPE_INTEGER),
                                            }
                                        )
                                    )
                            ),
                            "BRUNCH": openapi.Schema(
                                    type=openapi.TYPE_ARRAY,
                                    items=openapi.Schema(
                                        type=openapi.TYPE_ARRAY,
                                        items=openapi.Schema(
                                            type=openapi.TYPE_OBJECT,
                                            properties={
                                                "component_type": openapi.Schema(type=openapi.TYPE_STRING),
                                                "weight_min": openapi.Schema(type=openapi.TYPE_INTEGER),
                                                "weight_max": openapi.Schema(type=openapi.TYPE_INTEGER),
                                                "weight": openapi.Schema(type=openapi.TYPE_INTEGER),
                                            }
                                        )
                                    )
                            ),
                            "LUNCH": openapi.Schema(
                                    type=openapi.TYPE_ARRAY,
                                    items=openapi.Schema(
                                        type=openapi.TYPE_ARRAY,
                                        items=openapi.Schema(
                                            type=openapi.TYPE_OBJECT,
                                            properties={
                                                "component_type": openapi.Schema(type=openapi.TYPE_STRING),
                                                "weight_min": openapi.Schema(type=openapi.TYPE_INTEGER),
                                                "weight_max": openapi.Schema(type=openapi.TYPE_INTEGER),
                                                "weight": openapi.Schema(type=openapi.TYPE_INTEGER),
                                            }
                                        )
                                    )
                            ),
                            "MERIENDA": openapi.Schema(
                                    type=openapi.TYPE_ARRAY,
                                    items=openapi.Schema(
                                        type=openapi.TYPE_ARRAY,
                                        items=openapi.Schema(
                                            type=openapi.TYPE_OBJECT,
                                            properties={
                                                "component_type": openapi.Schema(type=openapi.TYPE_STRING),
                                                "weight_min": openapi.Schema(type=openapi.TYPE_INTEGER),
                                                "weight_max": openapi.Schema(type=openapi.TYPE_INTEGER),
                                                "weight": openapi.Schema(type=openapi.TYPE_INTEGER),
                                            }
                                        )
                                    )
                            ),
                            "DINNER": openapi.Schema(
                                    type=openapi.TYPE_ARRAY,
                                    items=openapi.Schema(
                                        type=openapi.TYPE_ARRAY,
                                        items=openapi.Schema(
                                            type=openapi.TYPE_OBJECT,
                                            properties={
                                                "component_type": openapi.Schema(type=openapi.TYPE_STRING),
                                                "weight_min": openapi.Schema(type=openapi.TYPE_INTEGER),
                                                "weight_max": openapi.Schema(type=openapi.TYPE_INTEGER),
                                                "weight": openapi.Schema(type=openapi.TYPE_INTEGER),
                                            }
                                        )
                                    )
                            ),
                        }
                    )
                ),
                400: 'Wrong date format. Must be YYYY-MM-DD',
            }
        },
        
        'GET /v1/profiles/':{
            'tags': ['Admin profiles'],
            'operation_summary': 'Получение списка пользователей',
            'operation_description': '',
            'responses': {
                200: openapi.Response(
                    'OK',
                    UserShortSerializer(many=True)
                ),
                400: 'Bad request',
            }
        },

        'POST /v1/profiles/images/custom/': {
            'tags': ['Profiles'],
            'operation_summary': 'Загрузка кастомной картинки в ленту фотографий.',
            'operation_description': '',
            'request_body': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        required=['image_info','image_data','image_type'],
                        properties={
                            "image_info": openapi.Schema(type=openapi.TYPE_STRING),
                            "image_data": openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_BASE64, description='base64'),
                            "image_type": openapi.Schema(type=openapi.TYPE_STRING, enum=['OTHER', 'GOALS', 'MEDICAL']),
                            
                        }
                    ),
            'responses': {
                201: 'Изображение сохранено',
                400: 'Неверные данные',
            }
        },

        'PATCH /v1/profiles/images/custom/{image_id}/': {
            'tags': ['Profiles'],
            'operation_summary': 'Изменяет данные картинки',
            'operation_description': 'В текущей реализации доступно изменение только подписи к картинке.\n\
                                    Изменять текст (подпись к картинке) можно в течение часа после загрузки.',
            'request_body': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        required=['image_info'],
                        properties={
                            "image_info": openapi.Schema(type=openapi.TYPE_STRING),
                        }
                    ),
            'responses': {
                201: 'Данные изображения изменены',
                400: 'Неверные данные',
                409: 'Невозможно изменить текст (доступное время для изменения уже истекло)'
            }
        },

        'GET /v1/profiles/{id}/': {
            'tags': ['Admin profiles'],
            'operation_summary': 'Получение пользователя',
            'operation_description': '',
            'responses': {
                200: openapi.Response(
                    'OK',
                    ProfileSerializer(many=True)
                ),
            }
        },

        'GET /v1/profiles/{user_id}/diary/': {
            'tags': ['Admin profiles'],
            'operation_summary': 'Получение дневника пользователя',
            'operation_description': '',
            'responses': {
                200: openapi.Response(
                    'OK',
                    DiaryRecordSerializer(many=True)
                ),
                404: 'Пользователь не найден'
            }
        },

        'GET /v1/profiles/{user_id}/diary/chart/': {
            'tags': ['Admin profiles'],
            'operation_summary': 'Получение данных статистики рациона',
            'operation_description': '',
            'responses': {
                200: openapi.Response(
                    'OK',
                    openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={

                            'weight': openapi.Schema(
                                        type=openapi.TYPE_ARRAY,
                                        items=openapi.Schema(
                                            type=openapi.TYPE_ARRAY,
                                            items=openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                                            )     
                            ),
                            "trueweight":openapi.Schema(
                                        type=openapi.TYPE_ARRAY,
                                        items=openapi.Schema(
                                            type=openapi.TYPE_ARRAY,
                                            items=openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                                            )     
                            ),
                            "steps":openapi.Schema(
                                        type=openapi.TYPE_ARRAY,
                                        items=openapi.Schema(
                                            type=openapi.TYPE_ARRAY,
                                            items=openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                                            )     
                            ),
                            "sleep":openapi.Schema(
                                        type=openapi.TYPE_ARRAY,
                                        items=openapi.Schema(
                                            type=openapi.TYPE_ARRAY,
                                            items=openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                                            )     
                            ),
                            "meals":openapi.Schema(
                                        type=openapi.TYPE_ARRAY,
                                        items=openapi.Schema(
                                            type=openapi.TYPE_ARRAY,
                                            items=openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                                            )     
                            ),
                            "faults": openapi.Schema(
                                        type=openapi.TYPE_ARRAY,
                                        items=openapi.Schema(
                                            type=openapi.TYPE_ARRAY,
                                            items=openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                                            )     
                            ),
                            "meal_reviewed":openapi.Schema(
                                        type=openapi.TYPE_ARRAY,
                                        items=openapi.Schema(
                                            type=openapi.TYPE_ARRAY,
                                            items=openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                                            )     
                            ),
                            "min_weight": openapi.Schema(type=openapi.TYPE_INTEGER),
                            "max_weight": openapi.Schema(type=openapi.TYPE_INTEGER),
                            "start_weight": openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                            "goal_weight": openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                            "start_date": openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT, description='milliseconds'),
                            "end_date": openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT, description='milliseconds'),
                        }
                    )
                ),
                404: 'Пользователь не найден'
            }
        },


        'GET /v1/profiles/{user_id}/diary/chart/full_points/':{
            'tags': ['Admin profiles'],
            'operation_summary': 'Получение данных статистики рациона вместе с пустыми днями',
            'operation_description': '',
            'responses': {
                200: openapi.Response(
                    'OK',
                    openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={

                            'weight': openapi.Schema(
                                        type=openapi.TYPE_ARRAY,
                                        items=openapi.Schema(
                                            type=openapi.TYPE_ARRAY,
                                            items=openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                                            )     
                            ),
                            "trueweight":openapi.Schema(
                                        type=openapi.TYPE_ARRAY,
                                        items=openapi.Schema(
                                            type=openapi.TYPE_ARRAY,
                                            items=openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                                            )     
                            ),
                            "steps":openapi.Schema(
                                        type=openapi.TYPE_ARRAY,
                                        items=openapi.Schema(
                                            type=openapi.TYPE_ARRAY,
                                            items=openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                                            )     
                            ),
                            "sleep":openapi.Schema(
                                        type=openapi.TYPE_ARRAY,
                                        items=openapi.Schema(
                                            type=openapi.TYPE_ARRAY,
                                            items=openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                                            )     
                            ),
                            "meals":openapi.Schema(
                                        type=openapi.TYPE_ARRAY,
                                        items=openapi.Schema(
                                            type=openapi.TYPE_ARRAY,
                                            items=openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                                            )     
                            ),
                            "faults": openapi.Schema(
                                        type=openapi.TYPE_ARRAY,
                                        items=openapi.Schema(
                                            type=openapi.TYPE_ARRAY,
                                            items=openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                                            )     
                            ),
                            "meal_reviewed":openapi.Schema(
                                        type=openapi.TYPE_ARRAY,
                                        items=openapi.Schema(
                                            type=openapi.TYPE_ARRAY,
                                            items=openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                                            )     
                            ),
                            "min_weight": openapi.Schema(type=openapi.TYPE_INTEGER),
                            "max_weight": openapi.Schema(type=openapi.TYPE_INTEGER),
                            "start_weight": openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                            "goal_weight": openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                            "start_date": openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT, description='milliseconds'),
                            "end_date": openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT, description='milliseconds'),
                        }
                    )
                ),
                404: 'Пользователь не найден'
            }
        },

    'GET /v1/profiles/{user_id}/ig/images/': {
            'tags': ['Admin profiles'],
            'operation_summary': 'Получение списка инстаграм фотографий пользователя',
            'manual_parameters': [
                openapi.Parameter('from', openapi.IN_QUERY, description='Кол-во секунд от 01.01.1970 00:00:00', type=openapi.TYPE_INTEGER),
                openapi.Parameter('to', openapi.IN_QUERY, description='Кол-во секунд от 01.01.1970 00:00:00', type=openapi.TYPE_INTEGER),
                ],
            'responses': {
                200: openapi.Response(
                    'OK',
                    InstagramImageSerializer(many=True)
                ),
            }
        },

    'GET /v1/profiles/{user_id}/ig/images/{hashtag}/': {
            'tags': ['Admin profiles'],
            'operation_summary': 'Получение списка инстаграм фотографий пользователя по хештегу',
            'responses': {
                200: openapi.Response(
                    'OK',
                    InstagramImageSerializer(many=True)
                ),
            }
        },

    'GET /v1/profiles/{user_id}/images/': {
            'tags': ['Admin profiles'],
            'operation_summary': 'Получение списка фотографий пользователя',
            'manual_parameters': [
                openapi.Parameter('from', openapi.IN_QUERY, description='Кол-во секунд от 01.01.1970 00:00:00', type=openapi.TYPE_INTEGER),
                openapi.Parameter('to', openapi.IN_QUERY, description='Кол-во секунд от 01.01.1970 00:00:00', type=openapi.TYPE_INTEGER),
                openapi.Parameter('page', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, default=1),
                openapi.Parameter('page_size', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, default=24),
                ],
            'responses': {
                200: openapi.Response(
                    'OK',
                    SRBCImageSerializer(many=True)
                ),
            }
        },

    'GET /v1/register/apple/': {
            'tags': ['Auth'],
            'operation_summary': 'Регистрация через Apple',
            'manual_parameters': [openapi.Parameter('token', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True)],
            'responses': {
                200: openapi.Response(
                    'OK',
                    openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'token': openapi.Schema(type=openapi.TYPE_STRING, description="JWT Токен"),
                        },
                    )
                ),
                403: 'Forbidden',
                400: "Bad request"
            }
        },

    'GET /v1/register/google/': {
            'tags': ['Auth'],
            'operation_summary': 'Регистрация через Google',
            'manual_parameters': [openapi.Parameter('token', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True)],
            'responses': {
                200: openapi.Response(
                    'OK',
                    openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'token': openapi.Schema(type=openapi.TYPE_STRING, description="JWT Токен"),
                        },
                    )
                ),
                403: 'Forbidden',
                400: "Bad request"
            }
        },

    'GET /v1/staff/tools/next_meal/': {
            'tags': ['Staff tools'],
            'operation_summary': 'Получение следующего рациона для анализа',
            'manual_parameters': [openapi.Parameter('mode', openapi.IN_QUERY, type=openapi.TYPE_STRING, enum=['NO', 'ANLZ_AUTO', 'ANLZ_MANUAL'], required=True)],
            'responses': {
                200: openapi.Response(
                    'OK',
                    openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "user_id": openapi.Schema(type=openapi.TYPE_INTEGER),
                            "meal_date": openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
                        },
                    )
                ),
            }
        },
        
    'POST /v1/stripe/subscription/change/': {
            'tags': ['Subscription'],
            'operation_summary': 'Сменить тариф',
            'manual_parameters': [openapi.Parameter('tariff', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True)],
            'responses': {
                200: 'OK',
            }
        },

    'POST /v1/stripe/subscription/create/checkout/': {
            'tags': ['Subscription'],
            'operation_summary': 'Оформить подписку',
            'manual_parameters': [openapi.Parameter('tariff', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True)],
            'responses': {
                200: 'OK',
            }
        },

    'POST /v1/subscription/cancel/': {
            'tags': ['Subscription'],
            'operation_summary': 'Отменить подписку',
            'responses': {
                200: 'OK',
            }
        },

    'POST /v1/yandex/subscription/create/checkout/': {
            'tags': ['Subscription'],
            'operation_summary': 'Оформить подписку через Yandex',
            'manual_parameters': [openapi.Parameter('tariff', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True)],
            'responses': {
                200: 'OK',
            }
        },
    
    'GET /v1/tasks/{task_id}/': {
            'tags': ['Tasks'],
            'operation_summary': 'Проверить статус таски',
            'responses': {
                200: openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "status": openapi.Schema(type=openapi.TYPE_STRING, default='pending'),
                        },
                    ),
                400: 'Bad request'
            }
        },

    'GET /v1/tg/channels/': {
            'tags': ['Telegram channel administration'],
            'operation_summary': 'Получение списка каналов в телеграме',
            'responses': {
                200: openapi.Response(
                    'OK',
                    TGChatSerializer(many=True)
                ),
            }
        },

    'GET /v1/tg/messages/': {
            'tags': ['Telegram channel administration'],
            'operation_summary': 'Получение списка сообщений в телеграме',
            'manual_parameters': [
                openapi.Parameter('channel_id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=True),
                openapi.Parameter('author_id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
                openapi.Parameter('answer_id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
                openapi.Parameter('message_type', openapi.IN_QUERY, type=openapi.TYPE_STRING, enum=[
                    'QUESTION',
                    'FEEDBACK',
                    'MEAL',
                    'FORMULA',
                ]),
                openapi.Parameter('status', openapi.IN_QUERY, type=openapi.TYPE_STRING, enum=[
                    'NEW',
                    'REJECTED',
                    'CANCELED',
                    'ANSWERED',
                    'POSTPONED',
                ]),
                
            ],
            'responses': {
                200: openapi.Response(
                    'OK',
                    TGMessageSerializer(many=True)
                ),
            }
        },

    'PUT /v1/tg/messages/': {
            'tags': ['Telegram channel administration'],
            'operation_summary': 'Опубликовать пост',
            'request_body': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        required=['post_id'],
                        properties={
                            "post_id": openapi.Schema(type=openapi.TYPE_INTEGER),
                            "channel_id": openapi.Schema(type=openapi.TYPE_INTEGER),
                            "additional_recipients": openapi.Schema(
                                type=openapi.TYPE_ARRAY, 
                                items=openapi.Schema(type=openapi.TYPE_STRING)
                            ),
                            "respond_to": openapi.Schema(
                                type=openapi.TYPE_ARRAY, 
                                items=openapi.Schema(type=openapi.TYPE_INTEGER)
                            ),
                            
                        }
                    ),
            'responses': {
                200: openapi.Response(
                    'OK',
                    TGMessageSerializer(many=True)
                ),
                400: openapi.Response(
                    'Bad request',
                    openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "error": openapi.Schema(type=openapi.TYPE_STRING)
                        }
                    ),
                ),
            }
        },
    
    'GET /v1/tg/messages/{message_id}/': {
            'tags': ['Telegram channel administration'],
            'operation_summary': 'Получение сообщения из телеграма',
            'responses': {
                200: openapi.Response(
                    'OK',
                    TGMessageSerializer
                ),
                404: 'Not found'
            }
        },
    
    'PUT /v1/tg/messages/{message_id}/': {
            'tags': ['Telegram channel administration'],
            'operation_summary': 'Редактировать сообщения из телеграма',
            'operation_id': 'v1_tg_messages_update_one',
            'request_body': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        required=['post_id'],
                        properties={
                            "status": openapi.Schema(type=openapi.TYPE_STRING,enum=[
                                'NEW',
                                'REJECTED',
                                'CANCELED',
                                'ANSWERED',
                                'POSTPONED',
                            ]),
                            "message_type": openapi.Schema(type=openapi.TYPE_STRING, enum=[
                                'QUESTION',
                                'FEEDBACK',
                                'MEAL',
                                'FORMULA',
                            ]),
                            
                        }
                    ),
            'responses': {
                200: openapi.Response(
                    'OK',
                    TGMessageSerializer
                ),
                404: 'Not found'
            }
        },
    
    'GET /v1/tg/posts/': {
            'tags': ['Telegram channel administration'],
            'operation_summary': 'Получение списка постов из телеграма',
            'manual_parameters': [
                openapi.Parameter('search', openapi.IN_QUERY, type=openapi.TYPE_STRING),
                openapi.Parameter('private', openapi.IN_QUERY, type=openapi.TYPE_BOOLEAN),
                openapi.Parameter('channel_id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
                openapi.Parameter('author_id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
                openapi.Parameter('is_private', openapi.IN_QUERY, type=openapi.TYPE_BOOLEAN),
            ],
            'responses': {
                200: openapi.Response(
                    'OK',
                    TGPostSerializer(many=True)
                ),
            }
        },

    'POST /v1/tg/posts/': {
            'tags': ['Telegram channel administration'],
            'operation_summary': 'Создание поста в телеграм',
            'manual_parameters': [
                openapi.Parameter('search', openapi.IN_QUERY, type=openapi.TYPE_STRING),
                openapi.Parameter('private', openapi.IN_QUERY, type=openapi.TYPE_BOOLEAN),
                openapi.Parameter('channel_id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
                openapi.Parameter('author_id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
                openapi.Parameter('is_private', openapi.IN_QUERY, type=openapi.TYPE_BOOLEAN),
            ],
            'request_body': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        required=['post'],
                        properties={
                            "post": openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                required=['text'],
                                properties={
                                    "text": openapi.Schema(type=openapi.TYPE_STRING),  
                                    'additional_recipients': openapi.Schema(
                                        type=openapi.TYPE_ARRAY,
                                        items=openapi.Schema(type=openapi.TYPE_STRING),
                                    ),
                                    'channel_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'is_private': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                    'image_url': openapi.Schema(type=openapi.TYPE_STRING),
                                    'sticker_data': openapi.Schema(
                                        type=openapi.TYPE_OBJECT,
                                        properties={
                                            'id': openapi.Schema(type=openapi.TYPE_INTEGER),                     
                                        }
                                    ),
                                    'respond_to': openapi.Schema(
                                        type=openapi.TYPE_ARRAY,
                                        items=openapi.Schema(type=openapi.TYPE_INTEGER),
                                    ),
                                }
                            ),                           
                        }
                    ),
            'responses': {
                200: openapi.Response(
                    'OK',
                    AddPostTelegramSwagger
                ),
                400: 'Bad request'
            }
        },

    'GET /v1/tg/posts/{post_id}/':  {
            'tags': ['Telegram channel administration'],
            'operation_summary': 'Получение поста из телеграма',
            'responses': {
                200: openapi.Response(
                    'OK',
                    TGPostSerializer
                ),
                404: 'Пост не найден'
            }
        },

    'PUT /v1/tg/posts/{post_id}/': {
            'tags': ['Telegram channel administration'],
            'operation_summary': 'Редактировать пост из телеграма',
            'request_body': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        required=['text'],
                        properties={
                            "text": openapi.Schema(type=openapi.TYPE_STRING),                           
                        }
                    ),
            'responses': {
                200: openapi.Response(
                    'OK',
                    TGPostSerializer
                ),
                400: 'Bad request'
            }
        },

    'GET /v1/tg/users/': {
            'tags': ['Telegram channel administration'],
            'operation_summary': 'Получение пользователей из телеграм канала ',
            'manual_parameters': [
                openapi.Parameter('channel_id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
            ],
             
            'responses': {
                200: openapi.Response(
                    'OK',
                    UserProfileSerializer(many=True)
                ),
            }
        },

    'GET /v1/tracker/mifit/load/': {
            'tags': ['Tracker'],
            'operation_summary': 'Не реализовано',  
            'responses': {
                200: openapi.Response(
                    'OK',
                ),
            }
        },

    'GET /v1/users/current/': {
            'tags': ['Auth'],
            'operation_summary': 'Получение текущего пользователя',  
            'responses': {
                200: openapi.Response(
                    'OK',
                    UserProfileSerializer
                ),
            }
        },

    
    'PUT /v2/diary/{diary_date}/meals/image/{meal_dt}/': {
            'tags': ['Diary'],
            'request_body': openapi.Schema(
                type=openapi.TYPE_OBJECT,
                required=['image', 'exif'],
                properties={
                    'image': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_BASE64, description='base64'),
                    'exif': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        required=[
                            'DateTime', 
                            'DateTimeOriginal', 
                            'Orientation', 
                            'DateTimeDigitized', 
                            'PreviewDateTime', 
                            'LensMake', 
                            'LensModel' ,
                            'Make', 
                            'Model', 
                            'GPSInfo'
                            ],
                        properties={
                            'DateTime': openapi.Schema(type=openapi.TYPE_STRING),
                            'DateTimeOriginal': openapi.Schema(type=openapi.TYPE_STRING),
                            'Orientation': openapi.Schema(type=openapi.TYPE_STRING),
                            'DateTimeDigitized': openapi.Schema(type=openapi.TYPE_STRING),
                            'PreviewDateTime': openapi.Schema(type=openapi.TYPE_STRING),
                            'LensMake': openapi.Schema(type=openapi.TYPE_STRING),
                            'LensModel': openapi.Schema(type=openapi.TYPE_STRING),
                            'Make': openapi.Schema(type=openapi.TYPE_STRING),
                            'Model': openapi.Schema(type=openapi.TYPE_STRING),
                            'GPSInfo': openapi.Schema(type=openapi.TYPE_STRING),
                        }
                    ),
                }
            ),
            'operation_summary': 'Загрузка на сервер фото приема пищи',
            'manual_parameters': [
                openapi.Parameter('diary_date', openapi.IN_PATH, description='Формат `%Y-%m-%d`', type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
                openapi.Parameter('meal_dt', openapi.IN_PATH, description='Формат `%Y-%m-%d_%H:%M:%S`', type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                ],
            'responses': {
                200: openapi.Response(
                    'OK',
                    DiaryMealDataAdminSerializer
                ),
                400: 'Bad request',
            }
        },

        'DELETE /v2/diary/{diary_date}/meals/image/{meal_dt}/': {
            'tags': ['Diary'],
            'operation_summary': 'Удаление фото приема пищи',
            'manual_parameters': [
                openapi.Parameter('diary_date', openapi.IN_PATH, description='Формат `%Y-%m-%d`', type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
                openapi.Parameter('meal_dt', openapi.IN_PATH, description='Формат `%Y-%m-%d_%H:%M:%S`', type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                ],
            'responses': {
                200: openapi.Response(
                    'OK',
                    DiaryMealDataAdminSerializer
                ),
                400: 'Bad request',
            }
        },

        'GET /v3/meetings/{meeting_id}/playlist.m3u8/': {
            'tags': ['Meetings'],
            'operation_summary': 'Получение списка чанков для лекции',
            'responses': {
                200: openapi.Response(
                    'Content-Type: application/vnd.apple.mpegurl',
                ),
                404: 'Not found',
            }
        },

        'GET /v3/meetings/{meeting_id}/chunks/{chunk_id}.ts/': {
            'tags': ['Meetings'],
            'operation_summary': 'Получение чанка лекции',
            'responses': {
                200: openapi.Response(
                    'Content-Type: audio/mpeg',
                ),
                404: 'Not found',
            }
        },

        'GET /v3/manual/': {
            'tags': ['Manual'],
            'operation_summary': 'Скачивание методички',
            'responses': {
                200: openapi.Response(
                    'Streaming Response',
                ),
                404: 'Not found',
            }
        },

    'GET /v3/profiles/usernote/': {
        'tags': ['Profiles'],
        'manual_parameters': [
                openapi.Parameter('page', openapi.IN_QUERY, description='Номер страницы', type=openapi.TYPE_INTEGER, default=1),
                openapi.Parameter('page_size', openapi.IN_QUERY, description='Кол-во рекомендаций на странице', type=openapi.TYPE_INTEGER, default=24),
                ],
        'operation_summary': 'Выводит список персональных рекомендаций',
        'operation_description': '',
    },

    'POST /v3/checkpoints/photos/': {
        'tags': ['Checkpoints'],
        'request_body': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        required=['face', 'side', 'rear'],
                        properties={
                            "face": openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                required=['image', 'exif'],
                                properties={
                                    "image": openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_BASE64, description='base64'),
                                    'exif':openapi.Schema(
                                        type=openapi.TYPE_OBJECT,
                                        required=['DateTimeOriginal', 'Orientation'],
                                        properties={
                                            'DateTime': openapi.Schema(type=openapi.TYPE_STRING), 
                                            'DateTimeOriginal': openapi.Schema(type=openapi.TYPE_STRING), 
                                            'Orientation': openapi.Schema(type=openapi.TYPE_STRING),
                                        }
                                    ),    
                                }
                            ),
                            'side': openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                required=['image', 'exif'],
                                properties={
                                    "image": openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_BASE64, description='base64'),
                                    'exif':openapi.Schema(
                                        type=openapi.TYPE_OBJECT,
                                        required=['DateTimeOriginal', 'Orientation'],
                                        properties={
                                            'DateTime': openapi.Schema(type=openapi.TYPE_STRING), 
                                            'DateTimeOriginal': openapi.Schema(type=openapi.TYPE_STRING), 
                                            'Orientation': openapi.Schema(type=openapi.TYPE_STRING),
                                        }
                                    ),    
                                }
                            ),
                            'rear': openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                required=['image', 'exif'],
                                properties={
                                    "image": openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_BASE64, description='base64'),
                                    'exif':openapi.Schema(
                                        type=openapi.TYPE_OBJECT,
                                        required=['DateTimeOriginal', 'Orientation'],
                                        properties={
                                            'DateTime': openapi.Schema(type=openapi.TYPE_STRING), 
                                            'DateTimeOriginal': openapi.Schema(type=openapi.TYPE_STRING), 
                                            'Orientation': openapi.Schema(type=openapi.TYPE_STRING),
                                        }
                                    ),    
                                }
                            ),
                            
                        }
                    ),
        'operation_summary': 'Добавление контрольных фотографий',
        'operation_description': '',
        'responses': {
                200: openapi.Response(
                    'Контрольные фотографии успешно загружены',
                ),
                400: openapi.Response(
                    'Bad request',
                    openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        required=[],
                        properties={
                            "code": openapi.Schema(type=openapi.TYPE_INTEGER),
                            "status": openapi.Schema(type=openapi.TYPE_STRING),
                            "message": openapi.Schema(type=openapi.TYPE_STRING),
                        },
                    ), 
                ),
            }
    },

    'GET /v3/diary/reports/': {
        'tags': ['Diary'],
        'manual_parameters': [
                openapi.Parameter('page', openapi.IN_QUERY, description='Номер страницы', type=openapi.TYPE_INTEGER, default=1),
                openapi.Parameter('page_size', openapi.IN_QUERY, description='Кол-во рекомендаций на странице', type=openapi.TYPE_INTEGER, default=5),
                ],
        'operation_summary': 'Выводит список отчетов пользователя',
        'operation_description': '',
    },

    'GET /v3/content/recipes/':{
        'tags': ['Recipes'],
        'manual_parameters': [
                openapi.Parameter('page', openapi.IN_QUERY, description='Номер страницы', type=openapi.TYPE_INTEGER, default=1),
                openapi.Parameter('page_size', openapi.IN_QUERY, description='Кол-во рекомендаций на странице', type=openapi.TYPE_INTEGER, default=24),
                openapi.Parameter('tags', openapi.IN_QUERY, type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_STRING)),
                openapi.Parameter('q', openapi.IN_QUERY, type=openapi.TYPE_STRING),
                ],
        'operation_summary': 'Выводит список рецептов',
        'operation_description': '',
    },

    'GET /v3/auth/telegram/': {
        'tags': ['Auth'],
        'manual_parameters': [
                openapi.Parameter('id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=True),
                openapi.Parameter('hash', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True),
                openapi.Parameter('auth_date', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=True),
                openapi.Parameter('username', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True),
                openapi.Parameter('last_name', openapi.IN_QUERY, type=openapi.TYPE_STRING),
                openapi.Parameter('first_name', openapi.IN_QUERY, type=openapi.TYPE_STRING),
                openapi.Parameter('photo_url', openapi.IN_QUERY, type=openapi.TYPE_STRING, format=openapi.FORMAT_URI),
                ],
        'operation_summary': 'Авторизация через Телеграмм',
        'operation_description': 'Надо передавать все параметры, которые придут из api Telegram',
        'responses': {
            200: openapi.Response('',
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'token': openapi.Schema(type=openapi.TYPE_STRING, description="JWT Токен"),
                    },
                )),
            403: openapi.Response('Forbidden', openapi.Schema(type=openapi.TYPE_STRING)),
            400: openapi.Response('Bad request', openapi.Schema(type=openapi.TYPE_STRING)),
        }
    },

    'GET /v3/register/telegram/': {
        'tags': ['Auth'],
        'manual_parameters': [
                openapi.Parameter('id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=True),
                openapi.Parameter('hash', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True),
                openapi.Parameter('auth_date', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=True),
                openapi.Parameter('username', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True),
                openapi.Parameter('last_name', openapi.IN_QUERY, type=openapi.TYPE_STRING),
                openapi.Parameter('first_name', openapi.IN_QUERY, type=openapi.TYPE_STRING),
                openapi.Parameter('photo_url', openapi.IN_QUERY, type=openapi.TYPE_STRING, format=openapi.FORMAT_URI),
                ],
        'operation_summary': 'Регистрация через Телеграмм',
        'operation_description': 'Надо передавать все параметры, которые придут из api Telegram',
        'responses': {
            200: openapi.Response('',
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'token': openapi.Schema(type=openapi.TYPE_STRING, description="JWT Токен"),
                    },
                )),
            403: openapi.Response('Forbidden', openapi.Schema(type=openapi.TYPE_STRING)),
            400: openapi.Response('Bad request', openapi.Schema(type=openapi.TYPE_STRING)),
        }
    },

    'GET /v3/staff/tools/users/': {
        'tags': ['Staff tools'],
        'operation_summary': 'Выводит список пользователей',
        'operation_description': '',
    },

    'GET /v3/staff/tools/waves/': {
        'tags': ['Staff tools'],
        'operation_summary': 'Выводит список потоков',
        'operation_description': '',
    },

    'POST /prodamus-notifications/': {
        'tags': ['Other'],
        'operation_summary': 'Метод для получения уведомлений об оплате с Prodamus',
        'operation_description': '',
    },

    'POST /api/v3/prodamus/payment/create/': {
        'tags': ['Payment'],
        'operation_summary': 'Создание ссылки для оплаты через Prodamus',
        'operation_description': '',
    #     user = forms.ModelChoiceField(label="Пользователь", queryset=User.objects.all())
    # tariff = forms.ModelChoiceField(label="Тариф", queryset=Tariff.objects.filter(is_archived=False))
    # wave = forms.ModelChoiceField(label="Поток", queryset=Wave.objects.filter(is_archived=False), required=False)
    # date_start = forms.DateField(label="Дата начала", widget=DateInput)
    # date_end = forms.DateField(label="Дата конца", widget=DateInput)
    # price_rub = forms.DecimalField(label="Цена в рублях" ,decimal_places=2)
        'request_body': openapi.Schema(
                type=openapi.TYPE_OBJECT,
                required=['user', 'tariff','date_start','date_end', 'price_rub'],
                properties={
                    'user': openapi.Schema(type=openapi.TYPE_INTEGER, description='User id'),
                    'tariff': openapi.Schema(type=openapi.TYPE_INTEGER, description='Tariff id'),
                    'wave': openapi.Schema(type=openapi.TYPE_INTEGER, description='Wave id'),
                    'date_start': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE, description='Формат `%Y-%m-%d`'),
                    'date_end': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE, description='Формат `%Y-%m-%d`'),
                    'price_rub': openapi.Schema(type=openapi.TYPE_NUMBER)
                }
            ),
        'responses': {
            200: openapi.Response('',
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'url': openapi.Schema(type=openapi.FORMAT_URI),
                    },
                )),
            403: openapi.Response('Forbidden', openapi.Schema(type=openapi.TYPE_STRING)),
            400: openapi.Response('Bad request', openapi.Schema(type=openapi.TYPE_STRING)),
        }
    }
        
    }
