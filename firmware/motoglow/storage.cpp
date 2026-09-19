#include "storage.h"
#include "config.h"
#include <EEPROM.h>

Settings g_settings;
static bool     s_dirty    = false;
static uint32_t s_dirtyAt  = 0;

static uint8_t checksumOf(const Settings& s) {
  const uint8_t* p = (const uint8_t*)&s;
  uint8_t sum = 0x5A;
  for (size_t i = 0; i < sizeof(Settings) - 1; i++) sum = (uint8_t)(sum * 31 + p[i]);
  return sum;
}

static void installDefaults() {
  g_settings.magic      = SETTINGS_MAGIC;
  g_settings.version    = SETTINGS_VERSION;
  g_settings.preset     = 0;
  g_settings.brightness = 2;   // third of four levels
  g_settings.speed      = 1;   // normal
  g_settings.checksum   = checksumOf(g_settings);
}

void settingsLoad() {
  EEPROM.begin(256);
  EEPROM.get(0, g_settings);
  if (g_settings.magic   != SETTINGS_MAGIC ||
      g_settings.version != SETTINGS_VERSION ||
      g_settings.checksum != checksumOf(g_settings)) {
    installDefaults();
  }
}

void settingsTouch() { s_dirty = true; s_dirtyAt = millis(); }

void settingsTick() {
  if (!s_dirty) return;
  if (millis() - s_dirtyAt < SETTINGS_SAVE_DELAY_MS) return;
  g_settings.magic    = SETTINGS_MAGIC;
  g_settings.version  = SETTINGS_VERSION;
  g_settings.checksum = checksumOf(g_settings);
  EEPROM.put(0, g_settings);
  EEPROM.commit();
  s_dirty = false;
}
