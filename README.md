# NormallogDashboard

## Getting started

```
pip install -r requirements.txt
streamlit run .\dashboardApp.py
```

## before anaalysis ##
```
1. message_key, message_value combine (nan value)
2. model, chipset, fw_version, sw_version, device_eco, device_type not need
3. meesage data handler need
```

## module analysis ##
```
 1. SAM
 2. voice
 3. admanager 
 4. com.webos.app.home -- NL_APP_LAUNCH, NL_QCARD_CLICKED, NL_HERO_SHOWN
 5. fancontroller -- NL_CHIP_THERMAL
 6. com.webos.app.homeconnect
 7. nudge
 8. AppInstallD -- NL_APP_INSTALLED
```

