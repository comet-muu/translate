from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator

from .models import Photo
from .forms import PhotoForm

from django.http import JsonResponse
from openai import OpenAI
from django.conf import settings
import tempfile

import base64,os
from django.core.files.base import ContentFile

client = OpenAI(
    api_key=settings.OPENAI_API_KEY
)
#language = "English"


@login_required
def ai_assistant(request):

    if request.method == 'POST':

        audio_file = request.FILES['audio']

        language = request.POST['language']

        mode = request.POST['mode']

        # 一時保存
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix='.webm'
        ) as temp_audio:

            for chunk in audio_file.chunks():

                temp_audio.write(chunk)

            temp_audio_path = temp_audio.name
        # Whisper音声認識
        with open(temp_audio_path, 'rb') as f:

            transcript = client.audio.transcriptions.create(

                model='whisper-1',

                file=f
            )

        os.remove(temp_audio_path)

        heard_text = transcript.text

        if mode == "reply":

            system_prompt = f"""
            The selected language is {language}.

            Generate exactly 3 natural replies.

            Output only the replies.
            """

        else:

            system_prompt = f"""
            The user speaks {language}.

            The transcript contains vocabulary words.

            Sometimes the final phrase is an instruction.

            Possible instructions:

            否定文
            疑問文
            過去形
            未来形
            丁寧
            カジュアル
            短文
            長文

            If the final phrase matches an instruction,
            treat it as an instruction.

            Otherwise treat all words as vocabulary.

            Create exactly 3 example sentences.

            Output language: English

            Use as many vocabulary words as possible.

            Output only the sentences.
            """

        # AI返答生成
        response = client.chat.completions.create(

            model='gpt-5.4-mini',

            messages=[

                {
                    "role": "system",

                    "content": system_prompt
                },

                {
                    "role": "user",

                    "content": heard_text
                }
            ]
        )

        replies = response.choices[0].message.content

        return JsonResponse({

            'heard': heard_text,

            'replies': replies
        })

    return render(
        request,
        'ai_assistant.html'
    )

def home(request):

    if request.user.is_authenticated:
        return render(request, 'mypage.html')

    return render(request, 'top.html')

@login_required
def mypage(request):

    return render(request, 'mypage.html')


@login_required
def photo_gallery(request):

    if request.method == 'POST':

        form = PhotoForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            photo = form.save(commit=False)

            photo.user = request.user

            photo.save()

            image_path = photo.image.path

            response = client.images.edit(
                model="gpt-image-1",

                image=open(image_path, "rb"),

                prompt="""
                    Convert this photograph into a clean manga-style illustration.
                    Black and white comic style.
                    Professional manga artwork.
                    """
            )

            image_bytes = base64.b64decode(
                response.data[0].b64_json
            )
            photo.manga_image.save(
                f'manga_{photo.id}.png',
                ContentFile(image_bytes),
                save=True
            )

            return redirect('/gallery/')

    else:

        form = PhotoForm()

    photos = Photo.objects.filter(
        user=request.user
    ).order_by('-created_at')

    paginator = Paginator(photos, 10)

    page_number = request.GET.get('page')

    page_obj = paginator.get_page(page_number)

    return render(
        request,
        'gallery.html',
        {
            'form': form,
            'page_obj': page_obj,
        }
    )

@login_required
def delete_photo(request, photo_id):

    if request.method == 'POST':

        photo = get_object_or_404(
            Photo,
            id=photo_id,
            user=request.user
        )

        photo.delete()

    return redirect('/gallery/')

@login_required
def delete_all_photos(request):

    if request.method == 'POST':

        photos = Photo.objects.filter(
            user=request.user
        )

        for photo in photos:

            photo.delete()

    return redirect('/gallery/')
