import discord
from discord.ext import commands
from discord import ui
import asyncio
import json
import os
import html
from datetime import datetime
from dotenv import load_dotenv


# =========================================================
# KONFIGURACJA
# =========================================================

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

# Kanał głównego panelu ticketów
TICKET_PANEL_CHANNEL_ID = 1547690637628018788

# Kategoria ticketów
TICKET_CATEGORY_ID = 1548654681461489765

# Kanał transcriptów
TRANSCRIPT_CHANNEL_ID = 1548678560800047145

# Kanał powitań
WELCOME_CHANNEL_ID = 1547356488530657331


# =========================================================
# ROLE
# =========================================================

# Rekrutacja
RECRUITMENT_ROLE_ID = 1546236770352365730

# Klatki + Inne
GENERAL_SUPPORT_ROLE_ID = 1546235991071658146

# Support do wszystkiego
UNIVERSAL_SUPPORT_ROLE_ID = 1548679652682240140


# =========================================================
# OBRAZKI
# =========================================================

# Panel ticketów
PANEL_IMAGE_URL = (
    "https://cdn.discordapp.com/attachments/1508833559551410198/"
    "1548676447579676672/"
    "Gemini_Generated_Image_8lu4pd8lu4pd8lu4.jpg"
    "?ex=6aa7ecd6&is=6aa69b56"
    "&hm=76ee4baf615ec0737403f12741f42168b7d6e3db24486e9460eced6071f95bb5"
)

# Ticket
TICKET_IMAGE_URL = PANEL_IMAGE_URL

# Powitanie
WELCOME_IMAGE_URL = (
    "https://cdn.discordapp.com/attachments/1508833559551410198/"
    "1548676441854705775/"
    "Gemini_Generated_Image_o4qcdio4qcdio4qc.jpg"
    "?ex=6aa7ecd4&is=6aa69b54"
    "&hm=562654d9233117f320f4f8bc738d14da08e8e8bffdc4d6252b63c16c077a0c&"
)

# Loader transcriptu
TRANSCRIPT_LOADING_IMAGE = (
    "https://cdn.discordapp.com/attachments/1508833559551410198/"
    "1548680146813325363/"
    "obraz_2026-09-13_143612130-removebg-preview.png"
    "?ex=6aa7f048&is=6aa69ec8"
    "&hm=bb0cce064bcc6c62ff5e903adfa486cfccfe13e4e051cde1f94596d1a341b760"
)


# =========================================================
# EMOJI
# =========================================================

ARROW = "<a:strzal:1548691719686459532>"
PONNY = "<:ponny:1548692409591009310>"


# =========================================================
# DANE
# =========================================================

DATA_DIR = "data"
PANEL_FILE = os.path.join(DATA_DIR, "panel.json")

os.makedirs(DATA_DIR, exist_ok=True)


# =========================================================
# INTENTS
# =========================================================

intents = discord.Intents.default()

intents.guilds = True
intents.members = True
intents.messages = True
intents.message_content = True


# =========================================================
# BOT
# =========================================================

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

views_registered = False


# =========================================================
# STATUS BOTA
# =========================================================

async def set_bot_status():

    await bot.change_presence(
        status=discord.Status.dnd,
        activity=discord.Game(
            name="Gildia Ponny Topka"
        )
    )

    print(
        "[STATUS] Nie przeszkadzać | Gildia Ponny Topka"
    )


# =========================================================
# PANEL JSON
# =========================================================

def save_panel_message_id(message_id: int):

    with open(
        PANEL_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            {
                "message_id": message_id
            },
            f
        )


def load_panel_message_id():

    if not os.path.exists(PANEL_FILE):
        return None

    try:

        with open(
            PANEL_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

        return data.get("message_id")

    except Exception:
        return None


# =========================================================
# ROLE / UPRAWNIENIA
# =========================================================

def is_universal_support(
    member: discord.Member
):

    return member.get_role(
        UNIVERSAL_SUPPORT_ROLE_ID
    ) is not None


def is_general_support(
    member: discord.Member
):

    return member.get_role(
        GENERAL_SUPPORT_ROLE_ID
    ) is not None


def is_recruitment_support(
    member: discord.Member
):

    return member.get_role(
        RECRUITMENT_ROLE_ID
    ) is not None


def can_close_ticket(
    member: discord.Member,
    ticket_type: str
):

    if is_universal_support(member):
        return True

    if is_general_support(member):
        return True

    if (
        ticket_type == "rekrutacja"
        and is_recruitment_support(member)
    ):
        return True

    return False


# =========================================================
# TYP TICKETU
# =========================================================

def get_ticket_type_from_channel(
    channel: discord.TextChannel
):

    topic = channel.topic or ""

    if "ticket_type=rekrutacja" in topic:
        return "rekrutacja"

    if "ticket_type=klatki" in topic:
        return "klatki"

    if "ticket_type=inne" in topic:
        return "inne"

    return None


# =========================================================
# OWNER ID
# =========================================================

def get_ticket_owner_id(
    channel: discord.TextChannel
):

    topic = channel.topic or ""

    for part in topic.split("|"):

        if part.startswith("owner_id="):

            try:
                return int(
                    part.split("=", 1)[1]
                )

            except ValueError:
                return None

    return None


# =========================================================
# NAZWA TICKETU
# =========================================================

def ticket_name(
    member: discord.Member,
    ticket_type: str
):

    category_name = {
        "klatki": "klatki",
        "rekrutacja": "rekrutacja",
        "inne": "inne"
    }.get(
        ticket_type,
        ticket_type
    )

    safe_name = (
        member.name
        .lower()
        .replace(" ", "-")
        .replace("_", "-")
    )

    return f"{category_name}-{safe_name}"[:90]


# =========================================================
# SPRAWDZENIE OTWARTEGO TICKETU
# =========================================================

async def user_has_open_ticket(
    guild: discord.Guild,
    user_id: int
):

    category = guild.get_channel(
        TICKET_CATEGORY_ID
    )

    if not isinstance(
        category,
        discord.CategoryChannel
    ):
        return None

    for channel in category.channels:

        if not isinstance(
            channel,
            discord.TextChannel
        ):
            continue

        owner_id = get_ticket_owner_id(
            channel
        )

        if owner_id == user_id:
            return channel

    return None


# =========================================================
# PANEL TICKETÓW
# COMPONENTS V2
# =========================================================

class TicketSelect(ui.Select):

    def __init__(self):

        options = [

            discord.SelectOption(
                label="Klatki",
                description="Pomoc związana z klatkami",
                value="klatki"
            ),

            discord.SelectOption(
                label="Rekrutacja",
                description="Złóż podanie do Ponny",
                value="rekrutacja"
            ),

            discord.SelectOption(
                label="Inne",
                description="Pozostałe sprawy",
                value="inne"
            )

        ]

        super().__init__(
            placeholder="Wybierz kategorię ticketu...",
            options=options,
            custom_id="ticket_category_select"
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):

        ticket_type = self.values[0]

        # =================================================
        # REKRUTACJA -> MODAL OD RAZU
        # =================================================

        if ticket_type == "rekrutacja":

            await interaction.response.send_modal(
                RecruitmentModal()
            )

            return

        # =================================================
        # KLATKI / INNE
        # =================================================

        await create_ticket(
            interaction,
            ticket_type
        )


class TicketPanelView(ui.LayoutView):

    def __init__(self):
        super().__init__(timeout=None)

        container = ui.Container()

        # ZDJĘCIE NA SAMEJ GÓRZE
        gallery = ui.MediaGallery()
        gallery.add_item(
            media=PANEL_IMAGE_URL
        )

        container.add_item(
            gallery
        )

        # TEKST
        container.add_item(
            ui.TextDisplay(
                content=(
                    "## ```🎀 System ticketów```\n"
                    f"{ARROW} ᴡʏʙɪᴇʀᴢ ᴏᴘᴄᴊᴇ ᴢ ᴍᴇɴᴜ ᴘᴏɴɪᴢᴇᴊ.\n"
                    f"{ARROW} ᴜᴢʏᴊ ᴘᴏᴘʀᴀᴡɴᴇᴊ ᴋᴀᴛᴇɢᴏʀɪɪ, "
                    "ᴢᴇʙʏ sᴢʏʙᴄɪᴇᴊ ᴘʀᴢᴇᴊsᴄ ᴘʀᴏᴄᴇs."
                )
            )
        )

        # SELECT MUSI BYĆ W ACTION ROW
        select_row = ui.ActionRow()

        select_row.add_item(
            TicketSelect()
        )

        container.add_item(
            select_row
        )

        self.add_item(
            container
        )


# =========================================================
# MODAL REKRUTACJI
# =========================================================

class RecruitmentModal(
    ui.Modal,
    title="Rekrutacja"
):

    age = ui.TextInput(
        label="Ile masz lat",
        placeholder="Wpisz swój wiek...",
        required=True,
        max_length=3
    )

    name = ui.TextInput(
        label="Imię",
        placeholder="Wpisz swoje imię...",
        required=True,
        max_length=50
    )

    minecraft = ui.TextInput(
        label="Nick Minecraft",
        placeholder="Wpisz swój nick Minecraft...",
        required=True,
        max_length=50
    )

    pvp = ui.TextInput(
        label="Twoje Pvp",
        placeholder="Np. 8/10",
        required=True,
        max_length=20
    )

    why = ui.TextInput(
        label="Dlaczego Ponny",
        placeholder="Dlaczego chcesz dołączyć do Ponny?",
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=500
    )

    async def on_submit(
        self,
        interaction: discord.Interaction
    ):

        existing = await user_has_open_ticket(
            interaction.guild,
            interaction.user.id
        )

        if existing:

            await interaction.response.send_message(
                f"Masz już otwarty ticket: {existing.mention}",
                ephemeral=True
            )

            return

        answers = {

            "age": self.age.value,

            "name": self.name.value,

            "minecraft": self.minecraft.value,

            "pvp": self.pvp.value,

            "why": self.why.value

        }

        await create_ticket_after_recruitment(
            interaction,
            answers
        )


# =========================================================
# PANEL W TICKETACH
# COMPONENTS V2
# =========================================================

class TicketActionView(
    ui.LayoutView
):

    def __init__(
        self,
        ticket_type: str,
        owner_mention: str,
        category_name: str,
        recruitment_answers=None
    ):

        super().__init__(
            timeout=None
        )

        container = ui.Container()

        # =================================================
        # ZDJĘCIE NA SAMEJ GÓRZE
        # =================================================

        gallery = ui.MediaGallery()

        gallery.add_item(
            media=TICKET_IMAGE_URL
        )

        container.add_item(
            gallery
        )

        # =================================================
        # NAGŁÓWEK
        # =================================================

        container.add_item(
            ui.TextDisplay(
                content=(
                    f"## **{owner_mention} × {category_name}**"
                )
            )
        )

        # =================================================
        # TREŚĆ
        # =================================================

        if ticket_type == "klatki":

            content = (
                f"{ARROW} Czekaj na odpowiedz Liderów"
            )

        elif ticket_type == "rekrutacja":

            a = recruitment_answers or {}

            content = (
                f"{PONNY} **Odpowiedzi:**\n\n"
                f"{ARROW} **Wiek:** {a.get('age', '-')}\n"
                f"{ARROW} **Imie:** {a.get('name', '-')}\n"
                f"{ARROW} **Nick Minecraft:** {a.get('minecraft', '-')}\n"
                f"{ARROW} **Twoje Pvp:** {a.get('pvp', '-')}\n"
                f"{ARROW} **Dlaczego Ponny:** {a.get('why', '-')}"
            )

        else:

            content = (
                f"{ARROW} Opisz dokładnie swoją sprawę. "
                "Osoba z supportu zajmie się Twoim zgłoszeniem "
                "tak szybko, jak to możliwe."
            )

        container.add_item(
            ui.TextDisplay(
                content=content
            )
        )

        # =================================================
        # PRZYCISKI
        # =================================================

        row = ui.ActionRow()

        row.add_item(
            CloseTicketButton(
                ticket_type
            )
        )

        row.add_item(
            AddPersonButton()
        )

        row.add_item(
            RemovePersonButton()
        )

        container.add_item(
            row
        )

        self.add_item(
            container
        )


# =========================================================
# ZAMKNIJ TICKET
# =========================================================

class CloseTicketButton(
    ui.Button
):

    def __init__(
        self,
        ticket_type
    ):

        super().__init__(
            label="ᴢᴀᴍᴋɴɪᴊ ᴛɪᴄᴋᴇᴛ",
            style=discord.ButtonStyle.secondary,
            custom_id="ticket_close"
        )

        self.ticket_type = ticket_type

    async def callback(
        self,
        interaction: discord.Interaction
    ):

        if not isinstance(
            interaction.user,
            discord.Member
        ):
            return

        if not can_close_ticket(
            interaction.user,
            self.ticket_type
        ):

            await interaction.response.send_message(
                "Nie masz uprawnień do zamknięcia tego ticketu.",
                ephemeral=True
            )

            return

        await interaction.response.send_message(
            "Czy na pewno chcesz zamknąć ten ticket?",
            view=CloseConfirmView(
                self.ticket_type
            ),
            ephemeral=True
        )


# =========================================================
# POTWIERDZENIE ZAMKNIĘCIA
# =========================================================

class CloseConfirmView(
    ui.View
):

    def __init__(
        self,
        ticket_type
    ):

        super().__init__(
            timeout=60
        )

        self.ticket_type = ticket_type

    @ui.button(
        label="TAK",
        style=discord.ButtonStyle.secondary
    )
    async def confirm_yes(
        self,
        interaction: discord.Interaction,
        button: ui.Button
    ):

        if not isinstance(
            interaction.user,
            discord.Member
        ):
            return

        if not can_close_ticket(
            interaction.user,
            self.ticket_type
        ):

            await interaction.response.send_message(
                "Nie masz uprawnień.",
                ephemeral=True
            )

            return

        await interaction.response.edit_message(
            content=(
                "Ticket zostanie zamknięty "
                "w przeciągu 10 sekund."
            ),
            view=None
        )

        channel = interaction.channel

        await asyncio.sleep(10)

        if not isinstance(
            channel,
            discord.TextChannel
        ):
            return

        try:

            await create_transcript(
                channel
            )

        except Exception as e:

            print(
                f"[TRANSCRIPT ERROR] {e}"
            )

        try:

            await send_owner_transcript_dm(
                channel
            )

        except Exception as e:

            print(
                f"[DM ERROR] {e}"
            )

        try:

            await channel.delete(
                reason="Ticket zamknięty"
            )

        except Exception as e:

            print(
                f"[DELETE ERROR] {e}"
            )

    @ui.button(
        label="NIE",
        style=discord.ButtonStyle.secondary
    )
    async def confirm_no(
        self,
        interaction: discord.Interaction,
        button: ui.Button
    ):

        await interaction.response.edit_message(
            content="Zamykanie ticketu anulowane.",
            view=None
        )


# =========================================================
# DODAJ OSOBĘ - MODAL
# =========================================================

class AddPersonModal(
    ui.Modal,
    title="Dodaj osobę"
):

    member_id = ui.TextInput(
        label="ID użytkownika",
        placeholder="Wpisz ID użytkownika Discord...",
        required=True,
        max_length=25
    )

    async def on_submit(
        self,
        interaction: discord.Interaction
    ):

        channel = interaction.channel

        if not isinstance(
            channel,
            discord.TextChannel
        ):
            return

        try:

            member_id = int(
                self.member_id.value
            )

        except ValueError:

            await interaction.response.send_message(
                "Nieprawidłowe ID użytkownika.",
                ephemeral=True
            )

            return

        member = interaction.guild.get_member(
            member_id
        )

        if not member:

            try:

                member = await interaction.guild.fetch_member(
                    member_id
                )

            except Exception:

                member = None

        if not member:

            await interaction.response.send_message(
                "Nie znaleziono takiego użytkownika.",
                ephemeral=True
            )

            return

        await channel.set_permissions(
            member,
            view_channel=True,
            send_messages=True,
            read_message_history=True,
            attach_files=True,
            embed_links=True
        )

        await interaction.response.send_message(
            f"Dodano {member.mention} do ticketu.",
            ephemeral=True
        )


# =========================================================
# DODAJ OSOBĘ - BUTTON
# =========================================================

class AddPersonButton(
    ui.Button
):

    def __init__(self):

        super().__init__(
            label="ᴅᴏᴅᴀᴊ ᴏsᴏʙᴇ̨",
            style=discord.ButtonStyle.secondary,
            custom_id="ticket_add_person"
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):

        if not isinstance(
            interaction.user,
            discord.Member
        ):
            return

        ticket_type = get_ticket_type_from_channel(
            interaction.channel
        )

        if not can_close_ticket(
            interaction.user,
            ticket_type or "inne"
        ):

            await interaction.response.send_message(
                "Nie masz uprawnień do zarządzania tym ticketem.",
                ephemeral=True
            )

            return

        await interaction.response.send_modal(
            AddPersonModal()
        )


# =========================================================
# USUŃ OSOBĘ - MODAL
# =========================================================

class RemovePersonModal(
    ui.Modal,
    title="Usuń osobę"
):

    member_id = ui.TextInput(
        label="ID użytkownika",
        placeholder="Wpisz ID użytkownika Discord...",
        required=True,
        max_length=25
    )

    async def on_submit(
        self,
        interaction: discord.Interaction
    ):

        channel = interaction.channel

        if not isinstance(
            channel,
            discord.TextChannel
        ):
            return

        try:

            member_id = int(
                self.member_id.value
            )

        except ValueError:

            await interaction.response.send_message(
                "Nieprawidłowe ID użytkownika.",
                ephemeral=True
            )

            return

        owner_id = get_ticket_owner_id(
            channel
        )

        if member_id == owner_id:

            await interaction.response.send_message(
                "Nie możesz usunąć właściciela ticketu.",
                ephemeral=True
            )

            return

        member = interaction.guild.get_member(
            member_id
        )

        if not member:

            try:

                member = await interaction.guild.fetch_member(
                    member_id
                )

            except Exception:

                member = None

        if not member:

            await interaction.response.send_message(
                "Nie znaleziono takiego użytkownika.",
                ephemeral=True
            )

            return

        await channel.set_permissions(
            member,
            overwrite=None
        )

        await interaction.response.send_message(
            f"Usunięto {member.mention} z ticketu.",
            ephemeral=True
        )


# =========================================================
# USUŃ OSOBĘ - BUTTON
# =========================================================

class RemovePersonButton(
    ui.Button
):

    def __init__(self):

        super().__init__(
            label="ᴜsᴜɴ́ ᴏsᴏʙᴇ̨",
            style=discord.ButtonStyle.secondary,
            custom_id="ticket_remove_person"
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):

        if not isinstance(
            interaction.user,
            discord.Member
        ):
            return

        ticket_type = get_ticket_type_from_channel(
            interaction.channel
        )

        if not can_close_ticket(
            interaction.user,
            ticket_type or "inne"
        ):

            await interaction.response.send_message(
                "Nie masz uprawnień do zarządzania tym ticketem.",
                ephemeral=True
            )

            return

        await interaction.response.send_modal(
            RemovePersonModal()
        )


# =========================================================
# TWORZENIE TICKETU
# =========================================================

async def create_ticket(
    interaction: discord.Interaction,
    ticket_type: str
):

    guild = interaction.guild

    if guild is None:
        return

    existing = await user_has_open_ticket(
        guild,
        interaction.user.id
    )

    if existing:

        await interaction.response.send_message(
            f"Masz już otwarty ticket: {existing.mention}",
            ephemeral=True
        )

        return

    category = guild.get_channel(
        TICKET_CATEGORY_ID
    )

    if not isinstance(
        category,
        discord.CategoryChannel
    ):

        await interaction.response.send_message(
            "Nie znaleziono kategorii ticketów.",
            ephemeral=True
        )

        return

    member = interaction.user

    overwrites = {

        guild.default_role:
            discord.PermissionOverwrite(
                view_channel=False
            ),

        member:
            discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                attach_files=True,
                embed_links=True
            )

    }

    # =====================================================
    # UNIVERSAL SUPPORT
    # =====================================================

    universal_role = guild.get_role(
        UNIVERSAL_SUPPORT_ROLE_ID
    )

    if universal_role:

        overwrites[universal_role] = (
            discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                manage_messages=True,
                attach_files=True,
                embed_links=True
            )
        )

    # =====================================================
    # GENERAL SUPPORT
    # =====================================================

    general_role = guild.get_role(
        GENERAL_SUPPORT_ROLE_ID
    )

    if general_role:

        overwrites[general_role] = (
            discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                manage_messages=True,
                attach_files=True,
                embed_links=True
            )
        )

    # =====================================================
    # REKRUTACJA
    # =====================================================

    if ticket_type == "rekrutacja":

        recruitment_role = guild.get_role(
            RECRUITMENT_ROLE_ID
        )

        if recruitment_role:

            overwrites[recruitment_role] = (
                discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True,
                    manage_messages=True,
                    attach_files=True,
                    embed_links=True
                )
            )

    topic = (
        f"ticket_type={ticket_type}"
        f"|owner_id={member.id}"
    )

    channel = await guild.create_text_channel(
        name=ticket_name(
            member,
            ticket_type
        ),
        category=category,
        overwrites=overwrites,
        topic=topic,
        reason="Utworzenie ticketu"
    )

    await interaction.response.send_message(
        f"Ticket został utworzony: {channel.mention}",
        ephemeral=True
    )

    # =====================================================
    # PING TYLKO WŁAŚCICIELA
    # =====================================================

    await channel.send(
        content=member.mention,
        allowed_mentions=discord.AllowedMentions(
            users=True,
            roles=False,
            everyone=False
        )
    )

    category_names = {

        "klatki": "Klatki",

        "rekrutacja": "Rekrutacja",

        "inne": "Inne"

    }

    await channel.send(
        view=TicketActionView(
            ticket_type=ticket_type,
            owner_mention=member.mention,
            category_name=category_names[ticket_type]
        )
    )


# =========================================================
# REKRUTACJA PO MODALU
# =========================================================

async def create_ticket_after_recruitment(
    interaction: discord.Interaction,
    answers: dict
):

    guild = interaction.guild

    if guild is None:
        return

    existing = await user_has_open_ticket(
        guild,
        interaction.user.id
    )

    if existing:

        await interaction.response.send_message(
            f"Masz już otwarty ticket: {existing.mention}",
            ephemeral=True
        )

        return

    category = guild.get_channel(
        TICKET_CATEGORY_ID
    )

    if not isinstance(
        category,
        discord.CategoryChannel
    ):

        await interaction.response.send_message(
            "Nie znaleziono kategorii ticketów.",
            ephemeral=True
        )

        return

    member = interaction.user

    overwrites = {

        guild.default_role:
            discord.PermissionOverwrite(
                view_channel=False
            ),

        member:
            discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                attach_files=True,
                embed_links=True
            )

    }

    # =====================================================
    # UNIVERSAL SUPPORT
    # =====================================================

    universal_role = guild.get_role(
        UNIVERSAL_SUPPORT_ROLE_ID
    )

    if universal_role:

        overwrites[universal_role] = (
            discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                manage_messages=True,
                attach_files=True,
                embed_links=True
            )
        )

    # =====================================================
    # GENERAL SUPPORT
    # =====================================================

    general_role = guild.get_role(
        GENERAL_SUPPORT_ROLE_ID
    )

    if general_role:

        overwrites[general_role] = (
            discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                manage_messages=True,
                attach_files=True,
                embed_links=True
            )
        )

    # =====================================================
    # RECRUITMENT SUPPORT
    # =====================================================

    recruitment_role = guild.get_role(
        RECRUITMENT_ROLE_ID
    )

    if recruitment_role:

        overwrites[recruitment_role] = (
            discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                manage_messages=True,
                attach_files=True,
                embed_links=True
            )
        )

    topic = (
        "ticket_type=rekrutacja"
        f"|owner_id={member.id}"
    )

    channel = await guild.create_text_channel(
        name=ticket_name(
            member,
            "rekrutacja"
        ),
        category=category,
        overwrites=overwrites,
        topic=topic,
        reason="Utworzenie ticketu rekrutacyjnego"
    )

    await interaction.response.send_message(
        f"Ticket rekrutacyjny został utworzony: {channel.mention}",
        ephemeral=True
    )

    # =====================================================
    # PING TYLKO UŻYTKOWNIKA
    # =====================================================

    await channel.send(
        content=member.mention,
        allowed_mentions=discord.AllowedMentions(
            users=True,
            roles=False,
            everyone=False
        )
    )

    await channel.send(
        view=TicketActionView(
            ticket_type="rekrutacja",
            owner_mention=member.mention,
            category_name="Rekrutacja",
            recruitment_answers=answers
        )
    )


# =========================================================
# TRANSCRIPT
# =========================================================

async def create_transcript(
    channel: discord.TextChannel
):

    transcript_channel = channel.guild.get_channel(
        TRANSCRIPT_CHANNEL_ID
    )

    if not isinstance(
        transcript_channel,
        discord.TextChannel
    ):
        return None

    messages = []

    async for message in channel.history(
        limit=None,
        oldest_first=True
    ):

        messages.append(
            message
        )

    owner_id = get_ticket_owner_id(
        channel
    )

    ticket_type = get_ticket_type_from_channel(
        channel
    )

    owner = None

    if owner_id:

        owner = channel.guild.get_member(
            owner_id
        )

    ticket_type_name = {

        "klatki": "Klatki",

        "rekrutacja": "Rekrutacja",

        "inne": "Inne"

    }.get(
        ticket_type,
        "Ticket"
    )

    rows = []

    for message in messages:

        timestamp = message.created_at.strftime(
            "%d.%m.%Y %H:%M"
        )

        author_name = html.escape(
            message.author.display_name
        )

        author_avatar = (
            message.author.display_avatar.url
            if message.author.display_avatar
            else ""
        )

        content = html.escape(
            message.content or ""
        ).replace(
            "\n",
            "<br>"
        )

        attachments_html = ""

        for attachment in message.attachments:

            url = html.escape(
                attachment.url,
                quote=True
            )

            filename = html.escape(
                attachment.filename
            )

            attachments_html += (
                f'<div class="attachment">'
                f'<a href="{url}" target="_blank">'
                f'📎 {filename}'
                f'</a>'
                f'</div>'
            )

        embeds_html = ""

        for embed in message.embeds:

            embed_parts = []

            if embed.title:

                embed_parts.append(
                    f'<div class="embed-title">'
                    f'{html.escape(embed.title)}'
                    f'</div>'
                )

            if embed.description:

                embed_parts.append(
                    f'<div class="embed-description">'
                    f'{html.escape(embed.description)}'
                    f'</div>'
                )

            for field in embed.fields:

                embed_parts.append(
                    f'<div class="embed-field">'
                    f'<strong>{html.escape(field.name)}</strong>'
                    f'<br>'
                    f'{html.escape(field.value)}'
                    f'</div>'
                )

            if embed.author and embed.author.name:

                embeds_html += (
                    '<div class="embed-author">'
                    f'{html.escape(embed.author.name)}'
                    '</div>'
                )

            embeds_html += (
                '<div class="discord-embed">'
                + "".join(embed_parts)
            )

            if embed.image and embed.image.url:

                embeds_html += (
                    f'<img class="embed-image" '
                    f'src="{html.escape(embed.image.url, quote=True)}">'
                )

            if embed.thumbnail and embed.thumbnail.url:

                embeds_html += (
                    f'<img class="embed-thumbnail" '
                    f'src="{html.escape(embed.thumbnail.url, quote=True)}">'
                )

            if embed.footer and embed.footer.text:

                embeds_html += (
                    '<div class="embed-footer">'
                    f'{html.escape(embed.footer.text)}'
                    '</div>'
                )

            embeds_html += "</div>"

        rows.append(
            f"""
            <div class="message">
                <img class="avatar" src="{html.escape(author_avatar, quote=True)}">

                <div class="message-content">

                    <div class="message-header">

                        <span class="author">
                            {author_name}
                        </span>

                        <span class="time">
                            {timestamp}
                        </span>

                    </div>

                    <div class="text">
                        {content}
                    </div>

                    {attachments_html}

                    {embeds_html}

                </div>
            </div>
            """
        )

    owner_display = (
        owner.display_name
        if owner
        else "Nieznany"
    )

    created_at = channel.created_at.strftime(
        "%d.%m.%Y %H:%M"
    )

    closed_at = datetime.now().strftime(
        "%d.%m.%Y %H:%M"
    )

    transcript_html = f"""
<!DOCTYPE html>

<html lang="pl">

<head>

<meta charset="UTF-8">

<meta name="viewport"
content="width=device-width, initial-scale=1.0">

<title>
Transcript - {html.escape(channel.name)}
</title>

<style>

* {{
    box-sizing: border-box;
}}

body {{
    margin: 0;
    background: #0d0d12;
    color: #f5f5f7;
    font-family: Arial, Helvetica, sans-serif;
}}

.loader {{
    position: fixed;
    inset: 0;
    background: #0d0d12;
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 9999;
    animation: fadeOut 2.5s ease forwards;
    animation-delay: 2s;
}}

.loader img {{
    width: 300px;
    height: 300px;
    object-fit: contain;
    animation: rotate 2s linear infinite;
}}

@keyframes rotate {{

    from {{
        transform: rotate(0deg);
    }}

    to {{
        transform: rotate(360deg);
    }}

}}

@keyframes fadeOut {{

    0% {{
        opacity: 1;
        visibility: visible;
    }}

    70% {{
        opacity: 1;
    }}

    100% {{
        opacity: 0;
        visibility: hidden;
    }}

}}

.header {{
    padding: 35px 20px;
    text-align: center;
}}

.header h1 {{
    margin: 0 0 10px;
    font-size: 30px;
}}

.header p {{
    margin: 5px 0;
    color: #aaa;
}}

.messages {{
    width: min(1000px, 95%);
    margin: auto;
    padding-bottom: 50px;
}}

.message {{
    display: flex;
    gap: 14px;
    padding: 15px;
    margin-bottom: 10px;
    background: #15151d;
    border-radius: 12px;
}}

.avatar {{
    width: 42px;
    height: 42px;
    border-radius: 50%;
    object-fit: cover;
}}

.message-content {{
    flex: 1;
    min-width: 0;
}}

.message-header {{
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 6px;
}}

.author {{
    font-weight: 700;
}}

.time {{
    color: #777;
    font-size: 12px;
}}

.text {{
    color: #ddd;
    line-height: 1.5;
    overflow-wrap: anywhere;
}}

.attachment {{
    margin-top: 8px;
}}

.attachment a {{
    color: #ff9fd3;
    text-decoration: none;
}}

.discord-embed {{
    margin-top: 10px;
    padding: 14px;
    background: #202028;
    border-left: 4px solid #ff8fc9;
    border-radius: 7px;
}}

.embed-title {{
    font-size: 18px;
    font-weight: 700;
    margin-bottom: 8px;
}}

.embed-description {{
    line-height: 1.5;
}}

.embed-field {{
    margin-top: 10px;
}}

.embed-author {{
    font-weight: 700;
    margin-bottom: 8px;
}}

.embed-image {{
    max-width: 100%;
    border-radius: 6px;
    margin-top: 12px;
}}

.embed-thumbnail {{
    max-width: 120px;
    border-radius: 6px;
    margin-top: 12px;
}}

.embed-footer {{
    margin-top: 12px;
    color: #888;
    font-size: 12px;
}}

.info {{
    width: min(1000px, 95%);
    margin: 0 auto 25px;
    padding: 18px;
    background: #15151d;
    border-radius: 12px;
}}

</style>

</head>

<body>

<div class="loader">

    <img src="{TRANSCRIPT_LOADING_IMAGE}">

</div>

<div class="header">

    <h1>
        Transcript — {html.escape(channel.name)}
    </h1>

    <p>
        Ticket: {html.escape(ticket_type_name)}
    </p>

</div>

<div class="info">

    <strong>Właściciel:</strong>
    {html.escape(owner_display)}

    <br>

    <strong>Utworzono:</strong>
    {created_at}

    <br>

    <strong>Zamknięto:</strong>
    {closed_at}

</div>

<div class="messages">

    {''.join(rows)}

</div>

</body>

</html>
"""

    safe_channel_name = "".join(
        c
        if c.isalnum() or c in "-_"
        else "_"
        for c in channel.name
    )

    filename = (
        f"transcript-{safe_channel_name}.html"
    )

    os.makedirs(
        "transcripts",
        exist_ok=True
    )

    filepath = os.path.join(
        "transcripts",
        filename
    )

    with open(
        filepath,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(
            transcript_html
        )

    file = discord.File(
        filepath,
        filename=filename
    )

    message = await transcript_channel.send(
        content=(
            f"📄 **Transcript:** `{channel.name}`\n"
            f"👤 **Właściciel:** "
            f"{owner.mention if owner else owner_display}\n"
            f"📁 **Kategoria:** {ticket_type_name}"
        ),
        file=file,
        allowed_mentions=discord.AllowedMentions(
            users=True,
            roles=False,
            everyone=False
        )
    )

    return message, filepath


# =========================================================
# TRANSCRIPT DOWNLOAD
# =========================================================

class TranscriptDownloadView(
    discord.ui.View
):

    def __init__(
        self,
        url: str
    ):

        super().__init__(
            timeout=None
        )

        self.add_item(
            discord.ui.Button(
                label="Pobierz transcript",
                style=discord.ButtonStyle.link,
                url=url
            )
        )


async def send_owner_transcript_dm(
    channel: discord.TextChannel
):

    owner_id = get_ticket_owner_id(
        channel
    )

    if not owner_id:
        return

    owner = channel.guild.get_member(
        owner_id
    )

    if not owner:

        try:

            owner = await channel.guild.fetch_member(
                owner_id
            )

        except Exception:

            return

    if not owner:
        return

    transcript_channel = channel.guild.get_channel(
        TRANSCRIPT_CHANNEL_ID
    )

    if not isinstance(
        transcript_channel,
        discord.TextChannel
    ):
        return

    messages = [
        message
        async for message
        in transcript_channel.history(
            limit=20
        )
    ]

    transcript_message = None

    for message in messages:

        if (
            bot.user
            and message.author.id == bot.user.id
            and message.attachments
        ):

            if channel.name in message.content:

                transcript_message = message

                break

    if not transcript_message:
        return

    attachment = (
        transcript_message.attachments[0]
    )

    try:

        await owner.send(
            content=(
                "💗 **Twój ticket został zamknięty.**\n\n"
                "Poniżej znajdziesz transcript rozmowy."
            ),
            view=TranscriptDownloadView(
                attachment.url
            )
        )

    except discord.Forbidden:

        print(
            f"Nie można wysłać DM do {owner}."
        )


# =========================================================
# POWITANIA
# COMPONENTS V2
# =========================================================

async def send_welcome(
    member: discord.Member
):

    channel = member.guild.get_channel(
        WELCOME_CHANNEL_ID
    )

    if not isinstance(
        channel,
        discord.TextChannel
    ):

        print(
            f"[WELCOME] Nie znaleziono kanału "
            f"{WELCOME_CHANNEL_ID}"
        )

        return

    # =====================================================
    # CONTAINER
    # =====================================================

    container = ui.Container()

    # =====================================================
    # ZDJĘCIE NA SAMEJ GÓRZE
    # =====================================================

    gallery = ui.MediaGallery()

    gallery.add_item(
        media=WELCOME_IMAGE_URL
    )

    container.add_item(
        gallery
    )

    # =====================================================
    # POWITANIE
    # =====================================================

    member_count = member.guild.member_count

    welcome_text = (
        "# ```🦄 GILDIA PONNY × WITAMY```\n"
        f"> {ARROW} Witaj {member.mention}\n"
        f"> {ARROW} Jestes **{member_count}** na naszym serwrze\n\n"
        f"> {ARROW} Mamy nadzieję, że zostaniesz z nami na dłużej."
    )

    container.add_item(
        ui.TextDisplay(
            content=welcome_text
        )
    )

    # =====================================================
    # LAYOUT VIEW
    # =====================================================

    view = ui.LayoutView(
        timeout=None
    )

    view.add_item(
        container
    )

    # =====================================================
    # WYSYŁKA
    # =====================================================

    await channel.send(
        view=view,
        allowed_mentions=discord.AllowedMentions(
            users=True,
            roles=False,
            everyone=False
        )
    )


# =========================================================
# NOWY CZŁONEK
# =========================================================

@bot.event
async def on_member_join(
    member: discord.Member
):

    try:

        await send_welcome(
            member
        )

    except Exception as e:

        print(
            f"[WELCOME ERROR] {e}"
        )


# =========================================================
# AUTOMATYCZNY PANEL
# =========================================================

async def ensure_ticket_panel():

    channel = bot.get_channel(
        TICKET_PANEL_CHANNEL_ID
    )

    if not isinstance(
        channel,
        discord.TextChannel
    ):

        print(
            "[TICKET PANEL] Nie znaleziono kanału."
        )

        return

    saved_id = load_panel_message_id()

    if saved_id:

        try:

            message = await channel.fetch_message(
                saved_id
            )

            if (
                message
                and bot.user
                and message.author.id == bot.user.id
            ):

                print(
                    "[TICKET PANEL] Panel już istnieje."
                )

                return

        except discord.NotFound:

            pass

        except discord.HTTPException:

            pass

    # =====================================================
    # NOWY PANEL
    # =====================================================

    message = await channel.send(
        view=TicketPanelView()
    )

    save_panel_message_id(
        message.id
    )

    print(
        f"[TICKET PANEL] Utworzono panel: "
        f"{message.id}"
    )


# =========================================================
# READY
# =========================================================

@bot.event
async def on_ready():

    global views_registered

    print(
        f"Zalogowano jako {bot.user} "
        f"(ID: {bot.user.id})"
    )

    # =====================================================
    # STATUS
    # =====================================================

    await set_bot_status()

    # ======================... (Pozostało: 1 KB)
