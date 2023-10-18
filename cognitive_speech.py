import os
import azure.cognitiveservices.speech as speechsdk


def generate_speech():
    SPEECH_KEY = "f0d702aa40ef48fcbf493ff5c7393e8b"
    SPEECH_LOCATION = "eastus"

    # This example requires environment variables named "SPEECH_KEY" and "SPEECH_REGION"
    speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_LOCATION)

    audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)
    speech_config.set_property(speechsdk.PropertyId.Speech_LogFilename, "SPEECH_LOG.txt")
    # The language of the voice that speaks.
    speech_config.speech_synthesis_voice_name='en-US-JennyNeural'
    #speech_config.set_property_by_name("OPENSSL_CONTINUE_ON_CRL_DOWNLOAD_FAILURE", "true")
    #speech_config.set_property_by_name("OPENSSL_DISABLE_CRL_CHECK", "true")
    speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

    # Get text from the console and synthesize to the default speaker.
    text = "JOIN THE GLORIOUS EVOLUTION"

    speech_synthesis_result = speech_synthesizer.speak_text_async(text).get()

    if speech_synthesis_result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        print("Speech synthesized for text [{}]".format(text))
    elif speech_synthesis_result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = speech_synthesis_result.cancellation_details
        print("Speech synthesis canceled: {}".format(cancellation_details.reason))
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            if cancellation_details.error_details:
                print("Error details: {}".format(cancellation_details.error_details))
                print("Did you set the speech resource key and region values?")