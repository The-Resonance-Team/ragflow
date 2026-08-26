import type { Translation } from '../translation-keys.ts';

export const vi: Translation = {
  collapse: 'Thu gọn',
  expand: 'Mở rộng',

  fieldDescriptionPlaceholder: 'Mô tả mục đích của trường này',
  fieldDelete: 'Xóa trường',
  fieldDescription: 'Mô tả',
  fieldDescriptionTooltip:
    'Thêm ngữ cảnh về ý nghĩa của trường này',
  fieldNameLabel: 'Tên trường',
  fieldNamePlaceholder: 'ví dụ: firstName, age, isActive',
  fieldNameTooltip:
    'Dùng camelCase để dễ đọc hơn (ví dụ: firstName)',
  fieldRequiredLabel: 'Trường bắt buộc',
  fieldType: 'Loại trường',
  fieldTypeExample: 'Ví dụ:',
  fieldTypeTooltipString: 'string: Văn bản',
  fieldTypeTooltipNumber: 'number: Số học',
  fieldTypeTooltipBoolean: 'boolean: Đúng/sai',
  fieldTypeTooltipObject: 'object: JSON lồng nhau',
  fieldTypeTooltipArray: 'array: Danh sách các giá trị',
  fieldAddNewButton: 'Thêm trường',
  fieldAddNewBadge: 'Trình dựng schema',
  fieldAddNewCancel: 'Hủy',
  fieldAddNewConfirm: 'Thêm trường',
  fieldAddNewDescription:
    'Tạo một trường mới cho JSON schema của bạn',
  fieldAddNewLabel: 'Thêm trường mới',

  fieldTypeTextLabel: 'Văn bản',
  fieldTypeTextDescription:
    'Cho các giá trị văn bản như tên, mô tả, v.v.',
  fieldTypeNumberLabel: 'Số',
  fieldTypeNumberDescription:
    'Cho số thập phân hoặc số nguyên',
  fieldTypeBooleanLabel: 'Có/Không',
  fieldTypeBooleanDescription: 'Cho giá trị đúng/sai',
  fieldTypeObjectLabel: 'Nhóm',
  fieldTypeObjectDescription:
    'Để nhóm các trường liên quan với nhau',
  fieldTypeArrayLabel: 'Danh sách',
  fieldTypeArrayDescription:
    'Cho tập hợp các phần tử',

  propertyDescriptionPlaceholder: 'Thêm mô tả...',
  propertyDescriptionButton: 'Thêm mô tả...',
  propertyRequired: 'Bắt buộc',
  propertyOptional: 'Tùy chọn',
  propertyDelete: 'Xóa trường',

  schemaEditorTitle: 'Trình soạn thảo JSON Schema',
  schemaEditorToggleFullscreen: 'Bật/tắt toàn màn hình',
  schemaEditorEditModeVisual: 'Trực quan',
  schemaEditorEditModeJson: 'JSON',

  arrayMinimumLabel: 'Số phần tử tối thiểu',
  arrayMinimumPlaceholder: 'Không giới hạn tối thiểu',
  arrayMaximumLabel: 'Số phần tử tối đa',
  arrayMaximumPlaceholder: 'Không giới hạn tối đa',
  arrayForceUniqueItemsLabel: 'Buộc các phần tử duy nhất',
  arrayItemTypeLabel: 'Loại phần tử',
  arrayValidationErrorMinMax:
    "'minItems' không thể lớn hơn 'maxItems'.",
  arrayValidationErrorContainsMinMax:
    "'minContains' không thể lớn hơn 'maxContains'.",

  booleanAllowFalseLabel: 'Cho phép giá trị sai',
  booleanAllowTrueLabel: 'Cho phép giá trị đúng',
  booleanNeitherWarning:
    'Cảnh báo: Bạn phải cho phép ít nhất một giá trị.',

  numberMinimumLabel: 'Giá trị tối thiểu',
  numberMinimumPlaceholder: 'Không giới hạn tối thiểu',
  numberMaximumLabel: 'Giá trị tối đa',
  numberMaximumPlaceholder: 'Không giới hạn tối đa',
  numberExclusiveMinimumLabel: 'Giá trị tối thiểu loại trừ',
  numberExclusiveMinimumPlaceholder:
    'Không có giá trị tối thiểu loại trừ',
  numberExclusiveMaximumLabel: 'Giá trị tối đa loại trừ',
  numberExclusiveMaximumPlaceholder:
    'Không có giá trị tối đa loại trừ',
  numberMultipleOfLabel: 'Bội số của',
  numberMultipleOfPlaceholder: 'Bất kỳ',
  numberAllowedValuesEnumLabel: 'Giá trị cho phép (enum)',
  numberAllowedValuesEnumNone:
    'Chưa đặt giá trị giới hạn nào',
  numberAllowedValuesEnumAddLabel: 'Thêm',
  numberAllowedValuesEnumAddPlaceholder:
    'Thêm giá trị cho phép...',
  numberValidationErrorMinMax:
    'Giá trị tối thiểu và tối đa phải nhất quán.',
  numberValidationErrorBothExclusiveAndInclusiveMin:
    "Không thể đặt đồng thời 'exclusiveMinimum' và 'minimum'.",
  numberValidationErrorBothExclusiveAndInclusiveMax:
    "Không thể đặt đồng thời 'exclusiveMaximum' và 'maximum'.",
  numberValidationErrorEnumOutOfRange:
    'Các giá trị enum phải nằm trong phạm vi đã định nghĩa.',

  objectPropertiesNone: 'Chưa định nghĩa thuộc tính nào',
  objectValidationErrorMinMax:
    "'minProperties' không thể lớn hơn 'maxProperties'.",

  stringMinimumLengthLabel: 'Độ dài tối thiểu',
  stringMinimumLengthPlaceholder: 'Không giới hạn tối thiểu',
  stringMaximumLengthLabel: 'Độ dài tối đa',
  stringMaximumLengthPlaceholder: 'Không giới hạn tối đa',
  stringPatternLabel: 'Mẫu (regex)',
  stringPatternPlaceholder: '^[a-zA-Z]+$',
  stringFormatLabel: 'Định dạng',
  stringFormatNone: 'Không',
  stringFormatDateTime: 'Ngày-Giờ',
  stringFormatDate: 'Ngày',
  stringFormatTime: 'Giờ',
  stringFormatEmail: 'Email',
  stringFormatUri: 'URI',
  stringFormatUuid: 'UUID',
  stringFormatHostname: 'Tên máy chủ',
  stringFormatIpv4: 'Địa chỉ IPv4',
  stringFormatIpv6: 'Địa chỉ IPv6',
  stringAllowedValuesEnumLabel: 'Giá trị cho phép (enum)',
  stringAllowedValuesEnumNone:
    'Chưa đặt giá trị giới hạn nào',
  stringAllowedValuesEnumAddPlaceholder:
    'Thêm giá trị cho phép...',
  stringValidationErrorLengthRange:
    "'Độ dài tối thiểu' không thể lớn hơn 'Độ dài tối đa'.",

  schemaTypeArray: 'Danh sách',
  schemaTypeBoolean: 'Có/Không',
  schemaTypeNumber: 'Số',
  schemaTypeObject: 'Đối tượng',
  schemaTypeString: 'Văn bản',
  schemaTypeNull: 'Rỗng',

  inferrerTitle: 'Suy diễn JSON Schema',
  inferrerDescription:
    'Dán tài liệu JSON của bạn bên dưới để tạo schema từ nó.',
  inferrerCancel: 'Hủy',
  inferrerGenerate: 'Tạo Schema',
  inferrerErrorInvalidJson:
    'Định dạng JSON không hợp lệ. Vui lòng kiểm tra đầu vào của bạn.',

  validatorTitle: 'Kiểm tra JSON',
  validatorDescription:
    'Dán tài liệu JSON của bạn để kiểm tra theo schema hiện tại. Việc kiểm tra diễn ra tự động khi bạn nhập.',
  validatorCurrentSchema: 'Schema hiện tại:',
  validatorContent: 'JSON của bạn:',
  validatorValid: 'JSON hợp lệ theo schema!',
  validatorErrorInvalidSyntax: 'Cú pháp JSON không hợp lệ',
  validatorErrorSchemaValidation: 'Lỗi xác thực schema',
  validatorErrorCount: 'Phát hiện {count} lỗi xác thực',
  validatorErrorPathRoot: 'Gốc',
  validatorErrorLocationLineAndColumn:
    'Dòng {line}, Cột {column}',
  validatorErrorLocationLineOnly: 'Dòng {line}',

  visualizerDownloadTitle: 'Tải xuống Schema',
  visualizerDownloadFileName: 'schema.json',
  visualizerSource: 'Nguồn JSON Schema',

  visualEditorNoFieldsHint1: 'Chưa định nghĩa trường nào',
  visualEditorNoFieldsHint2:
    'Thêm trường đầu tiên của bạn để bắt đầu',

  typeValidationErrorNegativeLength:
    'Giá trị độ dài không thể là số âm.',
  typeValidationErrorIntValue: 'Giá trị phải là số nguyên.',
  typeValidationErrorPositive: 'Giá trị phải là số dương.',
};
