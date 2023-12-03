var srbcApp = angular.module('srbcApp', [
    'ngTouch', 'ngSanitize', 'sticky',
    'ngAnimate',
    'ui.bootstrap',
    'ui.bootstrap.tpls',
    'ui.bootstrap.position',
    'ui.bootstrap.popover',
    'btford.markdown'
]);


// register the interceptor as a service
srbcApp.factory('httpApiInterceptor', ['$q', function ($q) {
    return {
        'response': function (response) {
            //console.log(response.data);
            if (response.data.code && response.data.status === 'error') {
                return $q.reject(response.data);
            }

            return response;
        },

        'responseError': function (rejection) {
            return $q.reject(rejection);
        }
    };
}]);

srbcApp.config(['$httpProvider',
    function ($httpProvider) {
        //$httpProvider.defaults.headers.common["X-Requested-With"] = 'XMLHttpRequest';
        $httpProvider.interceptors.push('httpApiInterceptor');
        $httpProvider.defaults.xsrfCookieName = 'csrftoken';
        $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
        $httpProvider.defaults.headers.common['X-Requested-With'] = 'XMLHttpRequest';
    }
]);

srbcApp.config(['$interpolateProvider',
    function ($interpolateProvider) {
        $interpolateProvider.startSymbol('{$');
        $interpolateProvider.endSymbol('$}');
    }
]);

srbcApp.controller('RootCtrl', [
        '$scope',
        '$http',
        '$window',
        '$timeout',
        '$location',
        function ($scope, $http, $window, $timeout, $location) {
            $scope.initiated = false;
            $scope.$root.channel = null;
            $scope.channels = [];
            $scope.show_post_preview = false;
            $scope.$root.alerts = [];
            $scope.messages = [];
            $scope.posts = [];
            $scope.selected_post = null;
            $scope.posts_filter_text = '';
            $scope.new_post_tpl = {
                "is_private": false,
                "is_posted": false,
                "text": ''
            };

            $scope.posts_filter_to = null;

            $scope.msgStatuses = {
                "NEW": "Неотвеченные сообщения",
                "ANSWERED": "Отвеченные сообщения",
                "CANCELED": "Пропущенные сообщения",
                "REJECTED": "Отклоненные сообщения",
                "POSTPONED": "Отложенные сообщения"
            };

            $scope.messagesGlobalFilter = {
                "status": "NEW"
            };

            $scope.postsSearchContext = function () {
                if ($scope.posts_filter_to) {
                    $timeout.cancel($scope.posts_filter_to)
                }

                $scope.posts_filter_to = $timeout(function () {
                    $scope.loadPosts();
                }, 300)
            };

            $scope.copyPostToForm = function (post) {
                if ($scope.new_post.text.length) {
                    $scope.new_post.text += '\n';
                }

                $scope.new_post.text += post.text;

                if (post.image_url) {
                    $scope.new_post.image_url = post.image_url;
                }
            };

            $scope.recentPostsSearchContext = function () {
                if ($scope.posts_filter_to) {
                    $timeout.cancel($scope.posts_filter_to)
                }

                $scope.posts_filter_to = $timeout(function () {
                    $scope.loadRecentPosts();
                }, 300)
            };

            $scope.getMessagesGlobalFilterStatusText = function () {
                if ($scope.messagesGlobalFilter.status) {
                    return $scope.msgStatuses[$scope.messagesGlobalFilter.status]
                } else {
                    return "Все сообщения"
                }
            };

            $scope.messages_filter = {
                "message_type": window.DEFAULT_MSG_TYPE_FILTER,
                "text": ''
            };

            $scope.posts_filter = {
                "is_private": false,
                "text": ''
            };

            $scope.new_post = {};

            $scope.new_post_init = function () {
                $scope.new_post = angular.copy($scope.new_post_tpl);
                if (sessionStorage.postDraft) {
                    $scope.new_post.text = sessionStorage.postDraft;
                }

            };

            $scope.$root.addAlert = function (message, type, timeout, callback) {
                if (angular.isUndefined(type)) {
                    type = 'default';
                }


                if (angular.isUndefined(timeout)) {
                    timeout = 0;
                }

                var _alert = {
                    "message": message,
                    "type": type,
                    "timeout": timeout
                };

                if (angular.isDefined(callback)) {
                    _alert['callback'] = callback;
                }

                $scope.$root.alerts.push(_alert);
                console.log($scope.$root.alerts);
            };

            $scope.$root.closeAlert = function (index) {
                $scope.$root.alerts.splice(index, 1);
            };

            $scope.savePostDraft = function () {
                sessionStorage.postDraft = $scope.new_post.text;
            };

            $scope.respondWithExisting = function () {
                var respond_to = [];
                for (var _i in $scope.messages) {
                    if ($scope.messages[_i].is_selected) {
                        respond_to.push($scope.messages[_i].id);
                    }
                }
                if (!respond_to.length && !$scope.new_post.additional_recipients) {
                    return
                }

                if (!$scope.selected_post) {
                    return
                }
                $http.put("/api/v1/tg/messages/", {
                    "post_id": $scope.selected_post.id,
                    "channel_id": $scope.$root.channel.id,
                    "respond_to": respond_to,
                    "additional_recipients": $scope.new_post.additional_recipients
                }).then(function (data) {
                    console.log(data);
                    $scope.$root.addAlert("Ответ был отправлен", "info", 5000);
                    $scope.new_post.additional_recipients = [];
                    $scope.loadUsersMessages();
                }, function (response) {
                    console.log(response);
                    var error_message = "Ошибка ответа на сообщение";
                    if (response.data && response.data.error) {
                        error_message = response.data.error;
                    }
                    $scope.$root.addAlert(error_message, "danger", 5000);

                })
            };

            $scope.prependQuestionText = function (text) {
                text = text.replace(/#вопрос/ig, "").replace(/([_*])/ig, "\\$1").trim();
                $scope.new_post.text = "_Вопрос:_ " + text + "\n\n" + "_Ответ:_ " + $scope.new_post.text;
            };

            $scope.prependFeedbackText = function (text) {
                text = text.replace(/#отзыв/ig, "").replace(/([_*])/ig, "\\$1").trim();
                $scope.new_post.text = "#отзыв: " + text + "\n\n" + "_Комментарий:_ " + $scope.new_post.text;
            };

            $scope.prependQuote = function (message) {
                if (message.message_type === 'QUESTION') {
                    $scope.prependQuestionText(message.text);
                } else if (message.message_type === 'FORMULA') {
                    $scope.prependQuestionText(message.text);
                } else if (message.message_type === 'MEAL') {
                    $scope.prependFeedbackText(message.text);
                } else if (message.message_type === 'FEEDBACK') {
                    $scope.prependFeedbackText(message.text);
                }
            };

            $scope.editPost = function (post) {
                post.dirty_text = angular.copy(post.text);
                post.is_edit = true;
            };

            $scope.setMessageStatusFilter = function (status) {
                if (status !== $scope.messagesGlobalFilter.status) {
                    $scope.messagesGlobalFilter.status = status;
                    $scope.loadUsersMessages();
                }
            };

            $scope.setMessageTypeFilter = function (message_type) {
                if (message_type !== $scope.messagesGlobalFilter.message_type) {
                    $scope.messagesGlobalFilter.message_type = message_type;
                } else {
                    delete $scope.messagesGlobalFilter.message_type;
                    delete $scope.messages_filter.message_type;
                }
                $scope.loadUsersMessages();
            };

            $scope.updatePost = function (post) {
                post.text = angular.copy(post.dirty_text);
                $http.put("/api/v1/tg/posts/" + post.id + "/", post).then(function (data) {
                    var post = angular.copy(data.data);
                    for (var _i in $scope.posts) {
                        if ($scope.posts[_i].id === post.id) {
                            $scope.posts[_i] = post;
                        }
                    }

                }, function (response) {
                    console.log(response);
                    var error_message = "Ошибка редактирования сообщения";
                    if (response.data && response.data.error) {
                        error_message = response.data.error;
                    }
                    $scope.$root.addAlert(error_message, "danger", 5000);

                })
            };

            $scope.resetPost = function (post) {
                post.is_edit = false;
            };

            $scope.respondWithNew = function () {
                var respond_to = [];
                for (var _i in $scope.messages) {
                    if ($scope.messages[_i].is_selected) {
                        respond_to.push($scope.messages[_i].id);
                    }
                }
                $scope.new_post.channel_id = $scope.$root.channel.id;
                $http.post("/api/v1/tg/posts/", {
                    "post": $scope.new_post,
                    "respond_to": respond_to
                }).then(function (data) {
                    console.log(data);
                    $scope.$root.addAlert("Ответ был отправлен", "info", 5000);
                    sessionStorage.postDraft = '';
                    $scope.new_post_init();
                    if (respond_to.length) {
                        $scope.loadUsersMessages();
                    }
                    $scope.loadPosts();
                }, function (response) {
                    console.log(response);
                    var error_message = "Ошибка ответа на сообщение";
                    if (response.data && response.data.error) {
                        error_message = response.data.error;
                    }
                    $scope.$root.addAlert(error_message, "danger", 5000);

                })
            };

            $scope.setSelectedPost = function (post) {
                console.log(post);
                $scope.selected_post = post;
            };

            $scope.setMessageAuthorFilter = function (value) {
                delete $scope.messagesGlobalFilter.status;
                delete $scope.messages_filter.status;
                delete $scope.messagesGlobalFilter.message_type;
                delete $scope.messages_filter.message_type;

                $scope.messagesGlobalFilter.author_id = value;

                $scope.messages_filter.text = '';

                $scope.loadUsersMessages();
            };

            $scope.setMessageStatus = function (message, new_status) {
                var new_message = angular.copy(message);
                new_message.status = new_status;
                $http.put("/api/v1/tg/messages/" + message.id + "/", new_message).then(function (data) {
                    message.status = data.data.status;
                }, function (response) {
                    console.log(response);
                    var error_message = "Ошибка редактирования сообщения";
                    if (response.data && response.data.error) {
                        error_message = response.data.error;
                    }
                    $scope.$root.addAlert(error_message, "danger", 5000);

                })
            };

            $scope.setMessageType = function (message, new_type) {
                var new_message = angular.copy(message);
                new_message.message_type = new_type;
                $http.put("/api/v1/tg/messages/" + message.id + "/", new_message).then(function (data) {
                    message.message_type = data.data.message_type;
                }, function (response) {
                    console.log(response);
                    var error_message = "Ошибка редактирования сообщения";
                    if (response.data && response.data.error) {
                        error_message = response.data.error;
                    }
                    $scope.$root.addAlert(error_message, "danger", 5000);

                })
            };


            $scope.resetMessagesGlobalFilter = function () {
                $scope.messagesGlobalFilter = {"status": 'NEW'};
                if ($scope.$root.channel) {
                    $scope.messagesGlobalFilter.channel_id = $scope.$root.channel.id;
                }
                $scope.messages_filter = {"message_type": window.DEFAULT_MSG_TYPE_FILTER};
                $scope.loadUsersMessages();
            };

            $scope.loadUsersMessages = function () {
                $scope.$root.is_messages_loading = true;

                $http.get("/api/v1/tg/messages/", {
                    "params": $scope.messagesGlobalFilter
                }).then(function (response) {
                    $scope.messages = response.data;
                    $scope.$root.is_messages_loading = false;
                }, function (response) {
                    console.log(response);
                    $scope.$root.is_messages_loading = false;
                    $scope.$root.addAlert("Ошибка загрузки сообщений", "danger", 5000);
                });
            };

            $scope.getChannels = function () {
                $http.get("/api/v1/tg/channels/", {}).then(function (response) {
                    $scope.channels = response.data;
                    if (!$scope.$root.channel) {
                        $scope.setActiveChannel($scope.channels[$scope.channels.length - 1]);
                    }
                }, function (response) {
                    console.log(response);
                    $scope.$root.addAlert("Ошибка загрузки списка каналов", "danger", 5000);
                });
            };

            $scope.setActiveChannel = function (channel) {
                if (angular.equals(channel, $scope.$root.channel)) {
                    return;
                }

                $scope.$root.channel = channel;
                $scope.messagesGlobalFilter.channel_id = $scope.$root.channel.id;
                $scope.resetMessagesGlobalFilter();
                $scope.loadUsersMessages();
                $scope.loadPosts();
                $scope.loadRecentPosts();
            };

            $scope.loadPosts = function () {
                var params = {};
                if ($scope.posts_filter_text.length) {
                    params['search'] = $scope.posts_filter_text
                }

                if ($scope.posts_filter.is_private) {
                    params['private'] = '';
                } else {
                    params['channel_id'] = $scope.$root.channel.id;
                }

                $http.get("/api/v1/tg/posts/", {
                    "params": params
                }).then(function (response) {
                    $scope.posts = response.data;
                }, function (response) {
                    console.log(response);
                    $scope.$root.addAlert("Ошибка загрузки сообщений", "danger", 5000);
                });
            };

            $scope.loadRecentPosts = function () {
                var params = {};
                if ($scope.posts_filter_text.length) {
                    params['search'] = $scope.posts_filter_text
                }

                if ($scope.posts_filter.is_private) {
                    params['private'] = '';
                }

                console.log(params);

                $http.get("/api/v1/tg/posts/", {
                    "params": params
                }).then(function (response) {
                    $scope.recent_posts = response.data;
                }, function (response) {
                    console.log(response);
                    $scope.$root.addAlert("Ошибка загрузки сообщений", "danger", 5000);
                });
            };
            $scope.new_post_init();
            $scope.getChannels();

        }
    ]
);

srbcApp.controller('ConfirmModalCtrl', ['$scope', '$uibModalInstance', function ($scope, $uibModalInstance, data) {
    $scope.ok = function () {
        $uibModalInstance.close(data);
    };

    $scope.cancel = function () {
        $uibModalInstance.dismiss('cancel');
    };
}]);

Date.prototype.addDays = function (days) {
    var dat = new Date(this.valueOf());
    dat.setDate(dat.getDate() + days);
    return dat;
};

Date.prototype.toSQL = function () {
    var mm = this.getMonth() + 1;
    var dd = this.getDate();

    return [this.getFullYear(),
        (mm > 9 ? '' : '0') + mm,
        (dd > 9 ? '' : '0') + dd
    ].join('-');
};
