#import <AVFoundation/AVFoundation.h>

// Эта функция будет ловить "прерывания" (звонки, Siri)
static void HandleInterruption(NSNotification *notification) {
    AVAudioSessionInterruptionType type = (AVAudioSessionInterruptionType)[notification.userInfo[AVAudioSessionInterruptionTypeKey] unsignedIntegerValue];
    
    if (type == AVAudioSessionInterruptionTypeEnded) {
        NSError *error = nil;
        AVAudioSession *session = [AVAudioSession sharedInstance];
        [session setActive:YES error:&error];
    }
}

// Эту функцию мы вызываем из C# (из Awake, OnApplicationFocus и после Microphone.End)
extern "C" void SetiOSAudioPlayback() {
    NSError *error = nil;
    AVAudioSession *session = [AVAudioSession sharedInstance];
    
    // --- ГЛАВНОЕ ИЗМЕНЕНИЕ: PlayAndRecord для поддержки микрофона ---
    // Игнорирует silent switch, mix с другими, default to speaker (не earpiece)
    [session setCategory:AVAudioSessionCategoryPlayAndRecord
                    mode:AVAudioSessionModeDefault
                 options:AVAudioSessionCategoryOptionMixWithOthers | AVAudioSessionCategoryOptionDefaultToSpeaker
                   error:&error];
    // --- КОНЕЦ ИЗМЕНЕНИЯ ---

    // Активируем сессию с новыми настройками
    [session setActive:YES error:&error];
    
    // Подписка на прерывания только один раз
    static dispatch_once_t onceToken;
    dispatch_once(&onceToken, ^{
        [[NSNotificationCenter defaultCenter] addObserverForName:AVAudioSessionInterruptionNotification
                                                          object:nil
                                                           queue:nil
                                                     usingBlock:^(NSNotification *notification) {
            HandleInterruption(notification);
        }];
    });
}