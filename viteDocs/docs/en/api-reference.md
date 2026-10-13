# Web API parameters

| API | Parameters |
| --- | --- |
| `PythonBootApplication` | `title`, `version`, `scan_packages`, `config_dir`, `auto_configure`, `exclude_auto_configurations`, `exclude`, and `**FastAPI options` |
| `create_app` | the above plus `exclude_modules` |
| `pythonboot_application` | `scan_packages`, `exclude_auto_configurations`, and `exclude` |
| `controller` | common Bean arguments, `prefix`, `tags`, and `**APIRouter options` |
| `controller_advise` | common Bean arguments |
| `route` | `path`, `methods`, and `**FastAPI add_api_route options` |
| `get/post/put/patch/delete` | `path` and `**FastAPI add_api_route options` |
| `exception_handler` | an exception type or integer status code |
| `inject` | `bean_type`, `name`, and `qualifier` |
| `date_time` | a non-empty `format` string |
| `ResponseContext.redirect` | `url` and `status_code` |
| `ResponseContext.set_cookie` | `key`, `value`, and `**SimpleCookie options` |

The common Bean arguments for `controller` and `controller_advise` are `name`, `init_method`, `destroy_method`, `lazy`, `scope`, `primary`, `qualifiers`, and `depends_on`. Import Web APIs from `pythonboot_web`; import core Bean declarations and `autowired()` from `pythonboot`.
