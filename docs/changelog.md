# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2022-11-28

---  
### Added

- Allow storage extra & headers attributes in [#18](https://github.com/jowilf/sqlalchemy-file/pull/18)


## [0.1.5] - 2022-10-15

---

### Added

- Add py.typed(PEP 561) in [#14](https://github.com/jowilf/sqlalchemy-file/pull/14)

## [0.1.4] - 2022-08-30

---

### Added

- Add `upload_storage` to the default information saved into the database. Before, `upload_storage` can be extracted
  from `path` attribute. Now you can access directly with `file['upload_storage']` in [#11](https://github.com/jowilf/sqlalchemy-file/pull/11)
- Accept additional metadata from `File` object in [#11](https://github.com/jowilf/sqlalchemy-file/pull/11)
- Add section [Upload File](https://jowilf.github.io/sqlalchemy-file/tutorial/using-files-in-models/#upload-file) to the
  documentation

## [0.1.3] - 2022-08-23

---

### Added
- Add `thumbnail_size` property to ImageField in [#9](https://github.com/jowilf/sqlalchemy-file/pull/9)

## [0.1.2] - 2022-08-11

---

### Added
- Add CHANGELOG.md
