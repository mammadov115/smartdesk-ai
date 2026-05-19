from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="companyprofile",
            name="chat_name",
            field=models.CharField(default="AI Assistant", max_length=255),
        ),
        migrations.AddField(
            model_name="companyprofile",
            name="greeting_message",
            field=models.TextField(default="Hello! How can I help you today?"),
        ),
        migrations.AddField(
            model_name="companyprofile",
            name="chat_language",
            field=models.CharField(
                blank=True,
                help_text="Language the AI should respond in (e.g. 'Azerbaijani'). Leave blank for default.",
                max_length=100,
            ),
        ),
    ]
