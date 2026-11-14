// Generated from backend OpenAPI. DO NOT EDIT. Source SHA256: b1226f19e1dc1e8ab7acc27be0d6c8f74fae19f66aa4313a7cb91ff0502a15ee
export interface paths {
  "/health": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Health */
    get: operations["health"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/c/{code}": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Short Link */
    get: operations["card_short_link"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/health": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Health */
    get: operations["api_health"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/auth/login": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** Login */
    post: operations["auth_login"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/admin/auth/login": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** Admin Login */
    post: operations["admin_auth_login"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/auth/change-password": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** Password Change */
    post: operations["auth_change_password"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/me/profile": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Profile */
    get: operations["me_profile"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/public/cards/{code}": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Public Card */
    get: operations["card_get_public"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/public/visitor/init": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** Visitor Init */
    post: operations["visitor_init"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/public/visits": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** Visit Create */
    post: operations["visit_create"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/public/visits/{id}": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    /** Visit Update */
    patch: operations["visit_update"];
    trace?: never;
  };
  "/api/v1/public/cards/{code}/vcard": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Vcard */
    get: operations["card_vcard"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/public/leads": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** Lead Create */
    post: operations["lead_create"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/public/chat/sessions": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** Session Create */
    post: operations["chat_session_create"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/public/chat/sessions/{id}/messages": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Message List */
    get: operations["chat_message_list"];
    put?: never;
    /**
     * Message Stream
     * @description SSE events: delta {text}; lead_prompt {reason,title}; done {message_id,kb_refs,nokb,model}; error {code,message}. 手机号只提示留资，绝不自动创建线索。
     */
    post: operations["chat_message_stream"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/public/messages/{id}/feedback": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** Feedback */
    post: operations["chat_feedback"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/me/card": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Card Get */
    get: operations["me_card_get"];
    /** Card Update */
    put: operations["me_card_update"];
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/me/card/share": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Card Share */
    get: operations["me_card_share"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/me/card/photo": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** Card Photo */
    post: operations["me_card_photo"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/me/card/wechat-qr": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** Card Wechat Qr */
    post: operations["me_card_wechat_qr"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/me/assistant": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Assistant Get */
    get: operations["me_assistant_get"];
    /** Assistant Update */
    put: operations["me_assistant_update"];
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/me/assistant/templates": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Assistant Templates */
    get: operations["me_assistant_templates"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/me/assistant/polish": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** Assistant Polish */
    post: operations["me_assistant_polish"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/me/leads": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Lead List */
    get: operations["me_lead_list"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/me/leads/{id}": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Lead Get */
    get: operations["me_lead_get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    /** Lead Update */
    patch: operations["me_lead_update"];
    trace?: never;
  };
  "/api/v1/me/stats": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Me Stats */
    get: operations["me_stats"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/me/visitors": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Visitor List */
    get: operations["me_visitor_list"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/me/visitors/{id}": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Visitor Get */
    get: operations["me_visitor_get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/me/notifications": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Notification List */
    get: operations["notification_list"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/me/notifications/unread-count": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Unread Count */
    get: operations["notification_unread_count"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/me/notifications/read-all": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** Read All */
    post: operations["notification_read_all"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/me/notifications/{id}/read": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** Read One */
    post: operations["notification_read"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/me/kb/notes": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Note List */
    get: operations["me_note_list"];
    put?: never;
    /** Note Create */
    post: operations["me_note_create"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/me/kb/notes/{file_id}": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Note Get */
    get: operations["me_note_get"];
    /** Note Update */
    put: operations["me_note_update"];
    post?: never;
    /** Note Delete */
    delete: operations["me_note_delete"];
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/me/kb/import": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** Kb Import */
    post: operations["me_kb_import"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/me/corrections": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Correction List */
    get: operations["me_correction_list"];
    put?: never;
    /** Correction Create */
    post: operations["me_correction_create"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/me/corrections/{id}": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    post?: never;
    /** Correction Delete */
    delete: operations["me_correction_delete"];
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/me/issues": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** Issue Create */
    post: operations["me_issue_create"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/me/test-chat/sessions": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** Test Session Create */
    post: operations["test_chat_session_create"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/me/test-chat/sessions/{id}/messages": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /**
     * Test Message Stream
     * @description SSE events: delta {text}; lead_prompt {reason,title}; done {message_id,kb_refs,nokb,model}; error {code,message}. 手机号只提示留资，绝不自动创建线索。
     */
    post: operations["test_chat_message_stream"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/public/campaigns/{id}": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Public Campaign */
    get: operations["campaign_get_public"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/me/campaigns": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** My Campaigns */
    get: operations["me_campaign_list"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/admin/company": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Company Get */
    get: operations["company_get"];
    /** Company Update */
    put: operations["company_update"];
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/admin/companies": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Company Options */
    get: operations["company_option_list"];
    put?: never;
    /** Company Create */
    post: operations["company_create"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/admin/companies/{id}": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Company Item Get */
    get: operations["company_item_get"];
    /** Company Item Update */
    put: operations["company_item_update"];
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/admin/product-cards": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Products */
    get: operations["product_card_list"];
    put?: never;
    /** Product Create */
    post: operations["product_card_create"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/admin/product-cards/{id}": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    /** Product Update */
    put: operations["product_card_update"];
    post?: never;
    /** Product Delete */
    delete: operations["product_card_delete"];
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/admin/employees": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Employees */
    get: operations["employee_list"];
    put?: never;
    /** Employee Create */
    post: operations["employee_create"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/admin/employees/import": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** Employee Import */
    post: operations["employee_import"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/admin/employees/{id}": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    /** Employee Update */
    put: operations["employee_update"];
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/admin/employees/{id}/reset-password": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** Employee Reset */
    post: operations["employee_reset_password"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/admin/employees/{id}/disable": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** Employee Disable */
    post: operations["employee_disable"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/admin/employees/{id}/transfer": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** Employee Transfer */
    post: operations["employee_transfer"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/admin/cards/{code}": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Card Get */
    get: operations["admin_card_get"];
    /** Card Update */
    put: operations["admin_card_update"];
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/admin/cards/{code}/assistant": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Assistant Get */
    get: operations["admin_card_assistant_get"];
    /** Assistant Update */
    put: operations["admin_card_assistant_update"];
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/admin/templates": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Templates */
    get: operations["template_list"];
    put?: never;
    /** Template Create */
    post: operations["template_create"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/admin/templates/{id}": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    /** Template Update */
    put: operations["template_update"];
    post?: never;
    /** Template Delete */
    delete: operations["template_delete"];
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/admin/templates/{id}/default": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    /** Template Default */
    put: operations["template_set_default"];
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/admin/stats": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Stats */
    get: operations["admin_stats"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/admin/leads": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Leads */
    get: operations["admin_lead_list"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/admin/kb/upload": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** Knowledge Upload */
    post: operations["kb_admin_upload"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/admin/kb/files": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Notes */
    get: operations["kb_admin_list"];
    put?: never;
    /** Note Create */
    post: operations["kb_admin_create"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/admin/kb/files/{file_id}": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Note Get */
    get: operations["kb_admin_get"];
    /** Note Update */
    put: operations["kb_admin_update"];
    post?: never;
    /** Note Delete */
    delete: operations["kb_admin_delete"];
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/admin/kb/files/{file_id}/history": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Note History */
    get: operations["kb_admin_history"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/admin/kb/files/{file_id}/rollback": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** Note Rollback */
    post: operations["kb_admin_rollback"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/admin/issues": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Issues */
    get: operations["issue_list"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/admin/issues/{id}": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    /** Issue Update */
    patch: operations["issue_update"];
    trace?: never;
  };
  "/api/v1/admin/rules": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Rules Get */
    get: operations["rules_get"];
    /** Rules Update */
    put: operations["rules_update"];
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/admin/runtime-settings": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Runtime Configuration */
    get: operations["runtime_settings_get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/admin/settings/{key}": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Settings Get */
    get: operations["settings_get"];
    /** Settings Update */
    put: operations["settings_update"];
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/admin/audit-logs": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Audit Logs */
    get: operations["audit_log_list"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/admin/notifications/broadcast": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** Broadcast */
    post: operations["notification_broadcast"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/admin/campaigns": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Campaigns */
    get: operations["campaign_list"];
    put?: never;
    /** Campaign Create */
    post: operations["campaign_create"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/admin/campaigns/{id}": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Campaign Get */
    get: operations["campaign_get"];
    /** Campaign Update */
    put: operations["campaign_update"];
    post?: never;
    /** Campaign Delete */
    delete: operations["campaign_delete"];
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/admin/campaigns/{id}/report": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Campaign Report */
    get: operations["campaign_report"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
}
export type webhooks = Record<string, never>;
export interface components {
  schemas: {
    /** AdminStats */
    AdminStats: {
      /** Source Breakdown */
      source_breakdown?: components["schemas"]["TrafficSource"][];
      /** Visits */
      visits: number;
      /** Visitors */
      visitors: number;
      /** Chats */
      chats: number;
      /** Leads */
      leads: number;
      /** Conversion Rate */
      conversion_rate: number;
      /** Daily */
      daily: components["schemas"]["DailyStat"][];
      /** Employees */
      employees: number;
      /** Cards */
      cards: number;
      /** Overdue Leads */
      overdue_leads: number;
    };
    /** AssistantData */
    AssistantData: {
      /** Template Id */
      template_id?: number | null;
      /**
       * Persona Extra
       * @default
       */
      persona_extra: string;
      /**
       * Opening
       * @default
       */
      opening: string;
      /** Guide Questions */
      guide_questions?: string[];
    };
    /** AssistantInput */
    AssistantInput: {
      /** Template Id */
      template_id?: number | null;
      /**
       * Persona Extra
       * @default
       */
      persona_extra: string;
      /**
       * Opening
       * @default
       */
      opening: string;
      /** Guide Questions */
      guide_questions?: string[];
    };
    /** AuditData */
    AuditData: {
      /** Id */
      id: number;
      /** Operator Id */
      operator_id: number;
      /** Action */
      action: string;
      /** Target */
      target: string;
      /** Detail */
      detail: {
        [key: string]: unknown;
      };
      /**
       * Created At
       * Format: date-time
       */
      created_at: string;
    };
    /** Body_employee_import */
    Body_employee_import: {
      /** File */
      file: string;
    };
    /** Body_kb_admin_upload */
    Body_kb_admin_upload: {
      /** Files */
      files: string[];
    };
    /** Body_me_card_photo */
    Body_me_card_photo: {
      /** File */
      file: string;
    };
    /** Body_me_card_wechat_qr */
    Body_me_card_wechat_qr: {
      /** File */
      file: string;
    };
    /** Body_me_kb_import */
    Body_me_kb_import: {
      /** File */
      file: string;
    };
    /** BroadcastInput */
    BroadcastInput: {
      /** Title */
      title: string;
      /** Content */
      content: string;
      /** Employee Ids */
      employee_ids?: number[] | null;
    };
    /** CampaignData */
    CampaignData: {
      /** Name */
      name: string;
      /**
       * Status
       * @default draft
       * @enum {string}
       */
      status: "draft" | "active" | "ended";
      /**
       * Start At
       * Format: date-time
       */
      start_at: string;
      /**
       * End At
       * Format: date-time
       */
      end_at: string;
      /**
       * Booth
       * @default
       */
      booth: string;
      /**
       * Location
       * @default
       */
      location: string;
      /**
       * Opening Override
       * @default
       */
      opening_override: string;
      /** Guide Override */
      guide_override?: string[];
      /** Id */
      id: number;
      /**
       * Created At
       * Format: date-time
       */
      created_at: string;
      /**
       * Updated At
       * Format: date-time
       */
      updated_at: string;
      /**
       * Is Live
       * @default false
       */
      is_live: boolean;
    };
    /** CampaignInput */
    CampaignInput: {
      /** Name */
      name: string;
      /**
       * Status
       * @default draft
       * @enum {string}
       */
      status: "draft" | "active" | "ended";
      /**
       * Start At
       * Format: date-time
       */
      start_at: string;
      /**
       * End At
       * Format: date-time
       */
      end_at: string;
      /**
       * Booth
       * @default
       */
      booth: string;
      /**
       * Location
       * @default
       */
      location: string;
      /**
       * Opening Override
       * @default
       */
      opening_override: string;
      /** Guide Override */
      guide_override?: string[];
    };
    /** CampaignReport */
    CampaignReport: {
      /** Campaign Id */
      campaign_id: number;
      /** Visits */
      visits: number;
      /** Visitors */
      visitors: number;
      /** Chats */
      chats: number;
      /** Leads */
      leads: number;
      /** Source Breakdown */
      source_breakdown: components["schemas"]["SourceBreakdownRow"][];
    };
    /** CardData */
    CardData: {
      /** Id */
      id: number;
      /** Code */
      code: string;
      /** Status */
      status: string;
      /** Employee Id */
      employee_id: number;
      /** Display Title */
      display_title: string;
      /** Mobile */
      mobile: string;
      /** Email */
      email: string;
      /** Intro */
      intro: string;
      /** Photo Url */
      photo_url: string;
      /** Photo Bg Url */
      photo_bg_url: string;
      /** Wechat Qr Url */
      wechat_qr_url: string;
      /**
       * Name
       * @default
       */
      name: string;
      /**
       * Dept
       * @default
       */
      dept: string;
      /**
       * Title
       * @default
       */
      title: string;
    };
    /** CardInput */
    CardInput: {
      /**
       * Display Title
       * @default
       */
      display_title: string;
      /**
       * Mobile
       * @default
       */
      mobile: string;
      /**
       * Email
       * @default
       */
      email: string;
      /**
       * Intro
       * @default
       */
      intro: string;
      /** Photo Url */
      photo_url?: string | null;
      /** Photo Bg Url */
      photo_bg_url?: string | null;
      /** Wechat Qr Url */
      wechat_qr_url?: string | null;
    };
    /** CompanyData */
    CompanyData: {
      /** Name */
      name: string;
      /**
       * Short Name
       * @default
       */
      short_name: string;
      /**
       * Intro
       * @default
       */
      intro: string;
      /**
       * Phone
       * @default
       */
      phone: string;
      /**
       * Address
       * @default
       */
      address: string;
      /**
       * Website
       * @default
       */
      website: string;
      /**
       * Logo Url
       * @default
       */
      logo_url: string;
      /**
       * Brand Color
       * @default
       */
      brand_color: string;
    };
    /** CompanyItem */
    CompanyItem: {
      /** Name */
      name: string;
      /**
       * Short Name
       * @default
       */
      short_name: string;
      /**
       * Intro
       * @default
       */
      intro: string;
      /**
       * Phone
       * @default
       */
      phone: string;
      /**
       * Address
       * @default
       */
      address: string;
      /**
       * Website
       * @default
       */
      website: string;
      /**
       * Logo Url
       * @default
       */
      logo_url: string;
      /**
       * Brand Color
       * @default
       */
      brand_color: string;
      /** Id */
      id: number;
      /** Is Primary */
      is_primary: boolean;
    };
    /** CompanyOption */
    CompanyOption: {
      /** Id */
      id: number;
      /** Name */
      name: string;
      /** Short Name */
      short_name: string;
      /** Is Primary */
      is_primary: boolean;
    };
    /** CorrectionData */
    CorrectionData: {
      /** Question */
      question: string;
      /** Correct Answer */
      correct_answer: string;
      /**
       * Wrong Answer
       * @default
       */
      wrong_answer: string;
      /**
       * Source
       * @default manual
       * @enum {string}
       */
      source: "test" | "visitor_chat" | "manual";
      /** Message Id */
      message_id?: number | null;
      /** Id */
      id: number;
    };
    /** CorrectionInput */
    CorrectionInput: {
      /** Question */
      question: string;
      /** Correct Answer */
      correct_answer: string;
      /**
       * Wrong Answer
       * @default
       */
      wrong_answer: string;
      /**
       * Source
       * @default manual
       * @enum {string}
       */
      source: "test" | "visitor_chat" | "manual";
      /** Message Id */
      message_id?: number | null;
    };
    /** CountData */
    CountData: {
      /** Count */
      count: number;
    };
    /** DailyStat */
    DailyStat: {
      /** Date */
      date: string;
      /** Visits */
      visits: number;
      /** Chats */
      chats: number;
      /** Leads */
      leads: number;
    };
    /** Draft */
    Draft: {
      /** Title */
      title: string;
      /** Content */
      content: string;
    };
    /** EmployeeImportResult */
    EmployeeImportResult: {
      /** Items */
      items: components["schemas"]["ImportRow"][];
    };
    /** EmployeeInput */
    EmployeeInput: {
      /** Name */
      name: string;
      /** Phone */
      phone?: string | null;
      /**
       * Dept
       * @default
       */
      dept: string;
      /**
       * Title
       * @default
       */
      title: string;
      /** Password */
      password?: string | null;
      /**
       * Role
       * @default employee
       * @enum {string}
       */
      role: "employee" | "admin";
      /**
       * Email
       * @default
       */
      email: string;
      /**
       * Business Scope
       * @default
       */
      business_scope: string;
      /** Company Id */
      company_id?: number | null;
    };
    /** EmployeeUpdate */
    EmployeeUpdate: {
      /** Name */
      name?: string | null;
      /** Phone */
      phone?: string | null;
      /** Dept */
      dept?: string | null;
      /** Title */
      title?: string | null;
      /** Email */
      email?: string | null;
      /** Business Scope */
      business_scope?: string | null;
      /** Role */
      role?: ("employee" | "admin") | null;
      /** Status */
      status?: ("active" | "disabled") | null;
      /** Company Id */
      company_id?: number | null;
    };
    /** Empty */
    Empty: Record<string, never>;
    /** FeedbackInput */
    FeedbackInput: {
      /**
       * Feedback
       * @default down
       * @constant
       */
      feedback: "down";
    };
    /** HTTPValidationError */
    HTTPValidationError: {
      /** Detail */
      detail?: components["schemas"]["ValidationError"][];
    };
    /** HealthData */
    HealthData: {
      /** Llm Mode */
      llm_mode: string;
      /**
       * Status
       * @default ok
       */
      status: string;
      /** Model */
      model: string;
    };
    /** HistoryData */
    HistoryData: {
      /** Revision */
      revision: number;
      /**
       * Title
       * @default
       */
      title: string;
      /**
       * Content
       * @default
       */
      content: string;
      /**
       * Public
       * @default false
       */
      public: boolean;
      /**
       * Approved
       * @default false
       */
      approved: boolean;
      /**
       * Hash
       * @default
       */
      hash: string;
    };
    /** ImportResult */
    ImportResult: {
      /** Drafts */
      drafts: components["schemas"]["Draft"][];
    };
    /** ImportRow */
    ImportRow: {
      /** Row */
      row: number;
      /** Ok */
      ok: boolean;
      /** Message */
      message: string;
      employee?: components["schemas"]["Staff"] | null;
    };
    /** IssueData */
    IssueData: {
      /** Id */
      id: number;
      /** Question */
      question: string;
      /** Type */
      type: string;
      /** Status */
      status: string;
      /** Count */
      count: number;
      /** Card Id */
      card_id: number;
      /**
       * Created At
       * Format: date-time
       */
      created_at: string;
    };
    /** IssueInput */
    IssueInput: {
      /** Question */
      question: string;
    };
    /** IssuePatch */
    IssuePatch: {
      /**
       * Status
       * @enum {string}
       */
      status: "open" | "resolved" | "ignored";
    };
    /** KnowledgeUploadDraft */
    KnowledgeUploadDraft: {
      /** Title */
      title: string;
      /** Content */
      content: string;
      /**
       * Public
       * @default false
       */
      public: boolean;
      /**
       * Approved
       * @default false
       */
      approved: boolean;
      /** File Id */
      file_id: string;
      /**
       * Description
       * @default
       */
      description: string;
      /**
       * Scope
       * @default company
       * @constant
       */
      scope: "company";
    };
    /** KnowledgeUploadResult */
    KnowledgeUploadResult: {
      /** Items */
      items: components["schemas"]["KnowledgeUploadRow"][];
    };
    /** KnowledgeUploadRow */
    KnowledgeUploadRow: {
      /** Filename */
      filename: string;
      /** Valid */
      valid: boolean;
      /** Message */
      message: string;
      draft?: components["schemas"]["KnowledgeUploadDraft"] | null;
    };
    /** LeadData */
    LeadData: {
      /** Campaign Id */
      campaign_id?: number | null;
      /**
       * Source
       * @default link
       */
      source: string;
      /** Visitor Id */
      visitor_id: number;
      /** Id */
      id: number;
      /** Name */
      name: string;
      /** Phone */
      phone: string;
      /** Company Name */
      company_name: string;
      /** Need */
      need: string;
      /**
       * Status
       * @enum {string}
       */
      status: "new" | "contacted" | "converted" | "invalid";
      /** Remark */
      remark: string;
      /**
       * Created At
       * Format: date-time
       */
      created_at: string;
      /** Card Id */
      card_id: number;
      /** Session Id */
      session_id: number | null;
    };
    /** LeadInput */
    LeadInput: {
      /** Campaign Id */
      campaign_id?: number | null;
      /** Visit Id */
      visit_id?: number | null;
      /**
       * Source
       * @default link
       * @enum {string}
       */
      source: "nfc" | "qr" | "poster" | "link" | "sig";
      /** Card Code */
      card_code: string;
      /** Session Id */
      session_id?: number | null;
      /** Name */
      name: string;
      /** Phone */
      phone: string;
      /**
       * Company Name
       * @default
       */
      company_name: string;
      /**
       * Need
       * @default
       */
      need: string;
      /**
       * Consent
       * @constant
       */
      consent: true;
    };
    /** LeadPatch */
    LeadPatch: {
      /** Status */
      status?: ("new" | "contacted" | "converted" | "invalid") | null;
      /** Remark */
      remark?: string | null;
    };
    /** LeadResult */
    LeadResult: {
      /** Id */
      id: number;
      /**
       * Status
       * @enum {string}
       */
      status: "new" | "contacted" | "converted" | "invalid";
    };
    /** LoginInput */
    LoginInput: {
      /** Phone */
      phone: string;
      /** Password */
      password: string;
    };
    /** LoginResult */
    LoginResult: {
      /** Token */
      token: string;
      /** Must Change Pwd */
      must_change_pwd: boolean;
      staff: components["schemas"]["Staff"];
    };
    /** MessageData */
    MessageData: {
      /** Id */
      id: number;
      /** Role */
      role: string;
      /** Content */
      content: string;
      /** Kb Refs */
      kb_refs: unknown[];
    };
    /** MessageInput */
    MessageInput: {
      /** Content */
      content: string;
    };
    /** NoteData */
    NoteData: {
      /** Title */
      title: string;
      /** Content */
      content: string;
      /**
       * Public
       * @default false
       */
      public: boolean;
      /**
       * Approved
       * @default false
       */
      approved: boolean;
      /**
       * Scope
       * @default company
       */
      scope: string;
      /** Card Code */
      card_code?: string | null;
      /** File Id */
      file_id: string;
      /** Revision */
      revision: number;
    };
    /** NoteInput */
    NoteInput: {
      /** Title */
      title: string;
      /** Content */
      content: string;
      /**
       * Public
       * @default false
       */
      public: boolean;
      /**
       * Approved
       * @default false
       */
      approved: boolean;
    };
    /** NotificationData */
    NotificationData: {
      /**
       * Target Type
       * @default
       */
      target_type: string;
      /** Target Id */
      target_id?: number | null;
      /** Id */
      id: number;
      /** Title */
      title: string;
      /** Content */
      content: string;
      /** Read At */
      read_at: string | null;
      /**
       * Created At
       * Format: date-time
       */
      created_at: string;
    };
    /** OK */
    OK: {
      /**
       * Ok
       * @default true
       */
      ok: boolean;
    };
    /** Page[AuditData] */
    Page_AuditData_: {
      /** Items */
      items: components["schemas"]["AuditData"][];
      /** Total */
      total: number;
      /** Page */
      page: number;
      /** Page Size */
      page_size: number;
    };
    /** Page[CampaignData] */
    Page_CampaignData_: {
      /** Items */
      items: components["schemas"]["CampaignData"][];
      /** Total */
      total: number;
      /** Page */
      page: number;
      /** Page Size */
      page_size: number;
    };
    /** Page[CorrectionData] */
    Page_CorrectionData_: {
      /** Items */
      items: components["schemas"]["CorrectionData"][];
      /** Total */
      total: number;
      /** Page */
      page: number;
      /** Page Size */
      page_size: number;
    };
    /** Page[IssueData] */
    Page_IssueData_: {
      /** Items */
      items: components["schemas"]["IssueData"][];
      /** Total */
      total: number;
      /** Page */
      page: number;
      /** Page Size */
      page_size: number;
    };
    /** Page[LeadData] */
    Page_LeadData_: {
      /** Items */
      items: components["schemas"]["LeadData"][];
      /** Total */
      total: number;
      /** Page */
      page: number;
      /** Page Size */
      page_size: number;
    };
    /** Page[MessageData] */
    Page_MessageData_: {
      /** Items */
      items: components["schemas"]["MessageData"][];
      /** Total */
      total: number;
      /** Page */
      page: number;
      /** Page Size */
      page_size: number;
    };
    /** Page[NoteData] */
    Page_NoteData_: {
      /** Items */
      items: components["schemas"]["NoteData"][];
      /** Total */
      total: number;
      /** Page */
      page: number;
      /** Page Size */
      page_size: number;
    };
    /** Page[NotificationData] */
    Page_NotificationData_: {
      /** Items */
      items: components["schemas"]["NotificationData"][];
      /** Total */
      total: number;
      /** Page */
      page: number;
      /** Page Size */
      page_size: number;
    };
    /** Page[Staff] */
    Page_Staff_: {
      /** Items */
      items: components["schemas"]["Staff"][];
      /** Total */
      total: number;
      /** Page */
      page: number;
      /** Page Size */
      page_size: number;
    };
    /** Page[VisitorData] */
    Page_VisitorData_: {
      /** Items */
      items: components["schemas"]["VisitorData"][];
      /** Total */
      total: number;
      /** Page */
      page: number;
      /** Page Size */
      page_size: number;
    };
    /** PasswordInput */
    PasswordInput: {
      /** Old Password */
      old_password: string;
      /** New Password */
      new_password: string;
    };
    /** PhotoData */
    PhotoData: {
      /** Photo Url */
      photo_url: string;
      /** Photo Bg Url */
      photo_bg_url: string;
    };
    /** PolishInput */
    PolishInput: {
      /** Text */
      text: string;
      /**
       * Field
       * @enum {string}
       */
      field:
        | "intro"
        | "persona_extra"
        | "opening"
        | "guide_questions"
        | "persona";
    };
    /** ProductData */
    ProductData: {
      /** Title */
      title: string;
      /**
       * Summary
       * @default
       */
      summary: string;
      /**
       * Image Url
       * @default
       */
      image_url: string;
      /**
       * Ask Question
       * @default
       */
      ask_question: string;
      /**
       * Sort
       * @default 0
       */
      sort: number;
      /**
       * Enabled
       * @default true
       */
      enabled: boolean;
      /** Id */
      id: number;
    };
    /** ProductInput */
    ProductInput: {
      /** Title */
      title: string;
      /**
       * Summary
       * @default
       */
      summary: string;
      /**
       * Image Url
       * @default
       */
      image_url: string;
      /**
       * Ask Question
       * @default
       */
      ask_question: string;
      /**
       * Sort
       * @default 0
       */
      sort: number;
      /**
       * Enabled
       * @default true
       */
      enabled: boolean;
    };
    /** PublicAssistant */
    PublicAssistant: {
      /** Opening */
      opening: string;
      /** Guide Questions */
      guide_questions: string[];
    };
    /** PublicCampaign */
    PublicCampaign: {
      /** Id */
      id: number;
      /** Name */
      name: string;
      /**
       * Start At
       * Format: date-time
       */
      start_at: string;
      /**
       * End At
       * Format: date-time
       */
      end_at: string;
      /**
       * Booth
       * @default
       */
      booth: string;
      /**
       * Location
       * @default
       */
      location: string;
    };
    /** PublicCard */
    PublicCard: {
      /** Code */
      code: string;
      /**
       * Status
       * @enum {string}
       */
      status: "active" | "disabled";
      /** Name */
      name?: string | null;
      /** Dept */
      dept?: string | null;
      /** Title */
      title?: string | null;
      /** Photo Url */
      photo_url?: string | null;
      /** Photo Bg Url */
      photo_bg_url?: string | null;
      /** Mobile */
      mobile?: string | null;
      /** Email */
      email?: string | null;
      /** Intro */
      intro?: string | null;
      /** Business Scope */
      business_scope?: string | null;
      /** Wechat Qr Url */
      wechat_qr_url?: string | null;
      company: components["schemas"]["CompanyData"];
      campaign?: components["schemas"]["PublicCampaign"] | null;
      /** Products */
      products?: components["schemas"]["ProductData"][];
      assistant?: components["schemas"]["PublicAssistant"] | null;
    };
    /** ResetPassword */
    ResetPassword: {
      /** Password */
      password: string;
    };
    /** RevisionInput */
    RevisionInput: {
      /** Revision */
      revision: number;
    };
    /** RulesData */
    RulesData: {
      /** Content */
      content: string;
    };
    /** RuntimeConfiguration */
    RuntimeConfiguration: {
      /** Settings */
      settings: {
        [key: string]: unknown;
      };
      /**
       * Limits Unit
       * @default messages_per_day
       * @constant
       */
      limits_unit: "messages_per_day";
    };
    /** SessionInput */
    SessionInput: {
      /** Card Code */
      card_code: string;
      /** Visit Id */
      visit_id?: number | null;
      /** Campaign Id */
      campaign_id?: number | null;
      /**
       * Source
       * @default link
       * @enum {string}
       */
      source: "nfc" | "qr" | "poster" | "link" | "sig";
    };
    /** SessionResult */
    SessionResult: {
      /** Opening */
      opening: string;
      /** Guide Questions */
      guide_questions: string[];
      /** Session Id */
      session_id: number;
      /** Visit Id */
      visit_id?: number | null;
      /** Campaign Id */
      campaign_id?: number | null;
      /**
       * Source
       * @default link
       * @enum {string}
       */
      source: "nfc" | "qr" | "poster" | "link" | "sig";
    };
    /** SettingData */
    SettingData: {
      /** Key */
      key: string;
      /** Value */
      value: unknown;
    };
    /** SettingInput */
    SettingInput: {
      /** Value */
      value?: unknown;
      /**
       * Clear Secret
       * @default false
       */
      clear_secret: boolean;
    };
    /** ShareData */
    ShareData: {
      /** Short Url */
      short_url: string;
      /** Qr Url */
      qr_url: string;
      /** Poster Url */
      poster_url: string;
    };
    /** SourceBreakdownRow */
    SourceBreakdownRow: {
      /** Source */
      source: string;
      /**
       * Visits
       * @default 0
       */
      visits: number;
      /**
       * Visitors
       * @default 0
       */
      visitors: number;
      /**
       * Chats
       * @default 0
       */
      chats: number;
      /**
       * Leads
       * @default 0
       */
      leads: number;
    };
    /** Staff */
    Staff: {
      /** Id */
      id: number;
      /** Name */
      name: string;
      /** Phone */
      phone?: string | null;
      /**
       * Role
       * @enum {string}
       */
      role: "employee" | "admin";
      /**
       * Dept
       * @default
       */
      dept: string;
      /**
       * Title
       * @default
       */
      title: string;
      /**
       * Email
       * @default
       */
      email: string;
      /**
       * Business Scope
       * @default
       */
      business_scope: string;
      /**
       * Status
       * @default active
       */
      status: string;
      /**
       * Must Change Pwd
       * @default false
       */
      must_change_pwd: boolean;
      /**
       * Card Code
       * @default
       */
      card_code: string;
      /**
       * Company Id
       * @default 0
       */
      company_id: number;
      /**
       * Company Name
       * @default
       */
      company_name: string;
      /**
       * Login Enabled
       * @default false
       */
      login_enabled: boolean;
    };
    /** StatsData */
    StatsData: {
      /** Source Breakdown */
      source_breakdown?: components["schemas"]["TrafficSource"][];
      /** Visits */
      visits: number;
      /** Visitors */
      visitors: number;
      /** Chats */
      chats: number;
      /** Leads */
      leads: number;
      /** Conversion Rate */
      conversion_rate: number;
      /** Daily */
      daily: components["schemas"]["DailyStat"][];
    };
    /** StayInput */
    StayInput: {
      /** Stay Seconds */
      stay_seconds: number;
    };
    /** TemplateData */
    TemplateData: {
      /** Name */
      name: string;
      /**
       * Persona
       * @default
       */
      persona: string;
      /**
       * Opening
       * @default
       */
      opening: string;
      /** Guide Questions */
      guide_questions?: string[];
      /**
       * Is Default
       * @default false
       */
      is_default: boolean;
      /**
       * Enabled
       * @default true
       */
      enabled: boolean;
      /** Id */
      id: number;
    };
    /** TemplateInput */
    TemplateInput: {
      /** Name */
      name: string;
      /**
       * Persona
       * @default
       */
      persona: string;
      /**
       * Opening
       * @default
       */
      opening: string;
      /** Guide Questions */
      guide_questions?: string[];
      /**
       * Is Default
       * @default false
       */
      is_default: boolean;
      /**
       * Enabled
       * @default true
       */
      enabled: boolean;
    };
    /** TextData */
    TextData: {
      /** Text */
      text: string;
    };
    /** TrafficSource */
    TrafficSource: {
      /** Source */
      source: string;
      /** Visits */
      visits: number;
      /** Visitors */
      visitors: number;
      /** Chats */
      chats: number;
      /** Leads */
      leads: number;
    };
    /** TransferInput */
    TransferInput: {
      /** To Employee Id */
      to_employee_id: number;
    };
    /** ValidationError */
    ValidationError: {
      /** Location */
      loc: (string | number)[];
      /** Message */
      msg: string;
      /** Error Type */
      type: string;
      /** Input */
      input?: unknown;
      /** Context */
      ctx?: Record<string, never>;
    };
    /** VisitInput */
    VisitInput: {
      /** Card Code */
      card_code: string;
      /**
       * Source
       * @enum {string}
       */
      source: "nfc" | "qr" | "poster" | "link" | "sig";
      /** Campaign Id */
      campaign_id?: number | null;
    };
    /** VisitResult */
    VisitResult: {
      /** Visit Id */
      visit_id: number;
      /** Campaign Id */
      campaign_id?: number | null;
    };
    /** VisitorData */
    VisitorData: {
      /** Id */
      id: number;
      /** Anon Id */
      anon_id: string;
      /**
       * Last Seen At
       * Format: date-time
       */
      last_seen_at: string;
    };
    /** VisitorDetail */
    VisitorDetail: {
      /** Id */
      id: number;
      /** Anon Id */
      anon_id: string;
      /**
       * Last Seen At
       * Format: date-time
       */
      last_seen_at: string;
      /** Visits */
      visits?: components["schemas"]["VisitorVisit"][];
      /** Sessions */
      sessions: components["schemas"]["VisitorSession"][];
    };
    /** VisitorInit */
    VisitorInit: {
      /** Anon Id */
      anon_id: string;
      /** Visitor Token */
      visitor_token: string;
    };
    /** VisitorSession */
    VisitorSession: {
      /**
       * Intent Level
       * @default C
       * @enum {string}
       */
      intent_level: "A" | "B" | "C";
      /** Tags */
      tags?: string[];
      /** Id */
      id: number;
      /** Summary */
      summary: string;
      /** Messages */
      messages: components["schemas"]["MessageData"][];
    };
    /** VisitorVisit */
    VisitorVisit: {
      /**
       * Source
       * @enum {string}
       */
      source: "nfc" | "qr" | "poster" | "link" | "sig";
      /**
       * Created At
       * Format: date-time
       */
      created_at: string;
      /** Stay Seconds */
      stay_seconds: number;
    };
    /** WechatQRData */
    WechatQRData: {
      /** Wechat Qr Url */
      wechat_qr_url: string;
    };
    /** DeltaEvent */
    DeltaEvent: {
      /** Text */
      text: string;
    };
    /** LeadPromptEvent */
    LeadPromptEvent: {
      /** Reason */
      reason: string;
      /** Title */
      title: string;
    };
    /** DoneEvent */
    DoneEvent: {
      /** Message Id */
      message_id: number;
      /** Kb Refs */
      kb_refs: unknown[];
      /** Nokb */
      nokb: boolean;
      /** Model */
      model: string;
    };
    /** ErrorEvent */
    ErrorEvent: {
      /** Code */
      code: string;
      /** Message */
      message: string;
    };
  };
  responses: never;
  parameters: never;
  requestBodies: never;
  headers: never;
  pathItems: never;
}
export type $defs = Record<string, never>;
export interface operations {
  health: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HealthData"];
        };
      };
    };
  };
  card_short_link: {
    parameters: {
      query?: {
        s?: "nfc" | "qr" | "poster" | "link" | "sig";
        e?: number | null;
      };
      header?: never;
      path: {
        code: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": unknown;
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  api_health: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HealthData"];
        };
      };
    };
  };
  auth_login: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["LoginInput"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["LoginResult"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  admin_auth_login: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["LoginInput"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["LoginResult"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  auth_change_password: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["PasswordInput"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["OK"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  me_profile: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Staff"];
        };
      };
    };
  };
  card_get_public: {
    parameters: {
      query?: {
        e?: number | null;
      };
      header?: never;
      path: {
        code: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["PublicCard"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  visitor_init: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["Empty"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["VisitorInit"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  visit_create: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["VisitInput"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["VisitResult"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  visit_update: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        id: number;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["StayInput"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["OK"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  card_vcard: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        code: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "text/plain": string;
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  lead_create: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["LeadInput"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["LeadResult"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  chat_session_create: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["SessionInput"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["SessionResult"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  chat_message_list: {
    parameters: {
      query?: {
        page?: number;
        page_size?: number;
      };
      header?: never;
      path: {
        id: number;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Page_MessageData_"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  chat_message_stream: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        id: number;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["MessageInput"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": unknown;
          "text/event-stream": string;
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  chat_feedback: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        id: number;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["FeedbackInput"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["OK"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  me_card_get: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["CardData"];
        };
      };
    };
  };
  me_card_update: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["CardInput"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["CardData"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  me_card_share: {
    parameters: {
      query?: {
        s?: "nfc" | "qr" | "poster" | "link" | "sig";
        e?: number | null;
      };
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ShareData"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  me_card_photo: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody: {
      content: {
        "multipart/form-data": components["schemas"]["Body_me_card_photo"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["PhotoData"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  me_card_wechat_qr: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody: {
      content: {
        "multipart/form-data": components["schemas"]["Body_me_card_wechat_qr"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["WechatQRData"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  me_assistant_get: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["AssistantData"];
        };
      };
    };
  };
  me_assistant_update: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["AssistantInput"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["AssistantData"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  me_assistant_templates: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["TemplateData"][];
        };
      };
    };
  };
  me_assistant_polish: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["PolishInput"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["TextData"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  me_lead_list: {
    parameters: {
      query?: {
        page?: number;
        page_size?: number;
        status?: string;
        q?: string;
      };
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Page_LeadData_"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  me_lead_get: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        id: number;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["LeadData"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  me_lead_update: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        id: number;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["LeadPatch"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["LeadData"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  me_stats: {
    parameters: {
      query?: {
        range?: string;
      };
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["StatsData"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  me_visitor_list: {
    parameters: {
      query?: {
        page?: number;
        page_size?: number;
      };
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Page_VisitorData_"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  me_visitor_get: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        id: number;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["VisitorDetail"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  notification_list: {
    parameters: {
      query?: {
        page?: number;
        page_size?: number;
        status?: string;
      };
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Page_NotificationData_"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  notification_unread_count: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["CountData"];
        };
      };
    };
  };
  notification_read_all: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["OK"];
        };
      };
    };
  };
  notification_read: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        id: number;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["OK"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  me_note_list: {
    parameters: {
      query?: {
        page?: number;
        page_size?: number;
      };
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Page_NoteData_"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  me_note_create: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["NoteInput"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["NoteData"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  me_note_get: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        file_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["NoteData"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  me_note_update: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        file_id: string;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["NoteInput"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["NoteData"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  me_note_delete: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        file_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["OK"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  me_kb_import: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody: {
      content: {
        "multipart/form-data": components["schemas"]["Body_me_kb_import"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ImportResult"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  me_correction_list: {
    parameters: {
      query?: {
        page?: number;
        page_size?: number;
      };
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Page_CorrectionData_"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  me_correction_create: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["CorrectionInput"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["CorrectionData"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  me_correction_delete: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        id: number;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["OK"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  me_issue_create: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["IssueInput"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["IssueData"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  test_chat_session_create: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["Empty"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["SessionResult"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  test_chat_message_stream: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        id: number;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["MessageInput"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": unknown;
          "text/event-stream": string;
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  campaign_get_public: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        id: number;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["PublicCampaign"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  me_campaign_list: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["PublicCampaign"][];
        };
      };
    };
  };
  company_get: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["CompanyData"];
        };
      };
    };
  };
  company_update: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["CompanyData"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["CompanyData"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  company_option_list: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["CompanyOption"][];
        };
      };
    };
  };
  company_create: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["CompanyData"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["CompanyItem"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  company_item_get: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        id: number;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["CompanyItem"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  company_item_update: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        id: number;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["CompanyData"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["CompanyItem"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  product_card_list: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ProductData"][];
        };
      };
    };
  };
  product_card_create: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["ProductInput"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ProductData"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  product_card_update: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        id: number;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["ProductInput"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ProductData"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  product_card_delete: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        id: number;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["OK"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  employee_list: {
    parameters: {
      query?: {
        page?: number;
        page_size?: number;
        q?: string;
      };
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Page_Staff_"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  employee_create: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["EmployeeInput"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Staff"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  employee_import: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody: {
      content: {
        "multipart/form-data": components["schemas"]["Body_employee_import"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["EmployeeImportResult"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  employee_update: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        id: number;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["EmployeeUpdate"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Staff"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  employee_reset_password: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        id: number;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["ResetPassword"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["OK"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  employee_disable: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        id: number;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["OK"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  employee_transfer: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        id: number;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["TransferInput"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["OK"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  admin_card_get: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        code: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["CardData"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  admin_card_update: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        code: string;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["CardInput"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["CardData"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  admin_card_assistant_get: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        code: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["AssistantData"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  admin_card_assistant_update: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        code: string;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["AssistantInput"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["AssistantData"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  template_list: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["TemplateData"][];
        };
      };
    };
  };
  template_create: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["TemplateInput"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["TemplateData"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  template_update: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        id: number;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["TemplateInput"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["TemplateData"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  template_delete: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        id: number;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["OK"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  template_set_default: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        id: number;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["TemplateData"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  admin_stats: {
    parameters: {
      query?: {
        range?: string;
      };
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["AdminStats"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  admin_lead_list: {
    parameters: {
      query?: {
        page?: number;
        page_size?: number;
        status?: string;
        q?: string;
      };
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Page_LeadData_"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  kb_admin_upload: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody: {
      content: {
        "multipart/form-data": components["schemas"]["Body_kb_admin_upload"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["KnowledgeUploadResult"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  kb_admin_list: {
    parameters: {
      query?: {
        page?: number;
        page_size?: number;
      };
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Page_NoteData_"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  kb_admin_create: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["NoteInput"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["NoteData"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  kb_admin_get: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        file_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["NoteData"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  kb_admin_update: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        file_id: string;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["NoteInput"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["NoteData"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  kb_admin_delete: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        file_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["OK"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  kb_admin_history: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        file_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HistoryData"][];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  kb_admin_rollback: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        file_id: string;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["RevisionInput"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["NoteData"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  issue_list: {
    parameters: {
      query?: {
        page?: number;
        page_size?: number;
        status?: string;
      };
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Page_IssueData_"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  issue_update: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        id: number;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["IssuePatch"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["IssueData"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  rules_get: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["RulesData"];
        };
      };
    };
  };
  rules_update: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["RulesData"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["RulesData"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  runtime_settings_get: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["RuntimeConfiguration"];
        };
      };
    };
  };
  settings_get: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        key: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["SettingData"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  settings_update: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        key: string;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["SettingInput"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["SettingData"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  audit_log_list: {
    parameters: {
      query?: {
        page?: number;
        page_size?: number;
      };
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Page_AuditData_"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  notification_broadcast: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["BroadcastInput"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["OK"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  campaign_list: {
    parameters: {
      query?: {
        page?: number;
        page_size?: number;
        status?: string;
      };
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Page_CampaignData_"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  campaign_create: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["CampaignInput"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["CampaignData"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  campaign_get: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        id: number;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["CampaignData"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  campaign_update: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        id: number;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["CampaignInput"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["CampaignData"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  campaign_delete: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        id: number;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["OK"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  campaign_report: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        id: number;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["CampaignReport"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
}
