from aiogram.utils.keyboard import InlineKeyboardBuilder
from db.models import UserSetting
from keyboards.callback import SettingsCallback


class SettingsKeyboards:
    @staticmethod
    def main_settings(settings: UserSetting):
        builder = InlineKeyboardBuilder()

        daily_status = "✅" if settings.daily_report_enabled else "❌"
        builder.button(
            text=f"Утренная рассылка:{daily_status}",
            callback_data=SettingsCallback(action="edit", value="daily_report").pack(),
        )

        rain_status = "✅" if settings.rain_alert_enabled else "❌"
        builder.button(
            text=f"Предупреждение о дожде:{rain_status}",
            callback_data=SettingsCallback(action="edit", value="rain_alert").pack(),
        )

        builder.button(
            text=f"Время утренней рассылки: {settings.report_time.strftime('%H:%M')}",
            callback_data=SettingsCallback(action="edit", value="report_time").pack(),
        )
        builder.button(
            text=f"Порог предупреждения о дожде: {settings.rain_threshold} мм/ч",
            callback_data=SettingsCallback(action="edit", value="rain_th").pack(),
        )

        builder.adjust(1)
        return builder.as_markup()
