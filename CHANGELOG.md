# Changelog

<!---
## 0.0.1 - 1970-01-01

### Added

- New stuff.

### Changed

- Changed stuff.

### Deprecated

- Deprecated stuff.

### Removed

- Removed stuff.

### Fixed

- Fixed stuff.

### Security

- Security related fix.
-->

## Unreleased

### Added

- You can now specify custom log format and log level in `dakara_base.config.create_logger` with arguments `custom_log_format` and `custom_log_level`.
- Access to and create user-level stored Dakara config files with `dakara_base.config.get_config_file` and `dakara_base.config.create_config_file`.

### Fixed

- `progress_bar`: the different progress bars have to be used as context managers (and not directly as iterators).
  See module help for examples.
  This fixes a bug when an exception raised within a progress bar would prevent to stop the capture of stderr, leading to hide any further log entry.

## 1.1.0 - 2019-09-16

### Added

* `progress_bar`: a collection of progress bars.

### Fixed

* Add `safe_workers` in the readme.

## 1.0.1 - 2019-09-08

### Fixed

- Fixed a bug when dealing with a HTTP route that does not have a content.

## 1.0.0 - 2019-07-20

Initial release.

### Added

* `config`: a configuration helper that can load an YAML file and manage loggers;
* `exceptions`: a base class for exceptions;
* `http_client`: an HTTP client dedicated to be used with an API;
* `resources_manager`: a helper for retreiving static files with module-like naming;
* `utils`: other various helpers;
* `websocket_client`: a Websocket client.
