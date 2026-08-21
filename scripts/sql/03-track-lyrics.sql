SET NAMES utf8mb4;

-- 02-data-mock.sql 실행 후, 트랙 가사만 별도로 업데이트할 때 사용합니다.
-- 각 CONCAT_WS('\n', ...) 안에 줄 단위로 가사를 붙여 넣으면 됩니다.
-- 작은따옴표(')가 들어간 줄은 SQL 문자열 안에서 두 번('') 써야 합니다.
-- 예: They can't -> 'They can''t'

SET @lyrics_track_1 = CONCAT_WS('\n',
    'Run like this, run, I
    Run like this, run, love you
    But you run like this, run like
    Run like this, run, love you
    Like
    Like
    Like
    Run like
    Like
    Like
    (Like, like, like)
    Run like this, run, I
    Run like this, run, love you
    But you run like this, run, I
    Run like this, run, love'
);

SET @lyrics_track_2 = CONCAT_WS('\n',
    'Come on, it’s gon be f hard

    Special edition and your AI couldn’t copy
    I’m leaving clues in the fitting room and it’s hot tea
    No I’m not thinking ’bout no exes know they miss me
    I got the whole room spinning like it’s tipsy

    Don’t bore us take you to the chorus
    Whooooooo wanna rock with Jennie
    Keep your hair done, nails done like Jennie
    Who else got ‘em obsessed like Jennie
    Like like like
    Jennie Jennie Jennie
    I think I really like
    Haters they don’t really like
    Cause they can never ever be
    But have you ever met
    Jennie Jennie Jennie Jennie
    Jennie
    It’s Jennie Jennie Jennie
    Jennie Jennie
    But have you ever met
    But have you ever met
    얼말 줘도 못해 서커스짓
    포징 한 번에 만들어 mosh pit
    They can’t deal with me cause I’m priceless
    여러 셀럽들 속에 내 DNA

    Get get outta my way
    바비가 처키가 되기 전에
    Name, shame, blame
    Tryna burst my bubble
    터트려봐 그럼 더 큰 홀에서
    만나는 거야 제니를

    Keep shading
    예술작품엔 필요해 frame이
    Ive slayed it, and I graved it
    Yes I’m guilty 잘난 게 죄니
    Whooooooo wanna rock with Jennie
    Keep you hair done, nails done like Jennie
    Who else got ’em obsessed like Jennie
    Like like like
    I think I really like Jennie
    Haters they don’t really like Jennie
    Cause they can never ever be Jennie
    But have you ever met
    Jennie Jennie Jennie
    Jennie Jennie Jennie Jennie
    It’s Jennie Jennie Jennie
    Jennie Jennie Jennie
    Jennie
    Like Jennie Jennie Jennie
    Jennie Jennie
    Rock with Jennie
    Keep your hair done, nails done like Jennie
    Who else got ’em obsessed like
    But have you ever met Jennie
    But have you ever met
    Jennie Jennie Jennie
    It’s Jennie Jennie Jennie Jennie'
);

SET @lyrics_track_3 = CONCAT_WS('\n',
    'You know for me, there’s no breakin’ point
    Yeah, I’ma be here through all that noise
    I’m gon’ protect what’s mine only
    You know the role you’re playin’
    I’m not sayin’ we ain’t got problems
    Know that we could both be on one
    But if somebody try to start some
    I’m gon’ try for you
    I’ll fight for you, go off for you
    I’ll start a war
    Ever since the day we locked in
    I was gonna be a down bitch
    If I need to start a war
    I’m gon’ try for you
    I’ll fight for you, go off for you
    I’ll start a war
    Yeah, yeah, yeah
    ’Cause love, it hold responsibility
    Hold you down, you hold me down
    That’s just how we been rollin’
    Feelin’ like that first hit that you take in the mornin’
    Baby, you a token
    And I think I’ve grown ’til somebody comes for you
    I could bring the heat if I needed to (to)
    It ain’t like I’ll do it, but you know I’ma prove it
    Oh, if I need to do anything for you
    I’m not sayin’ we ain’t got problems
    Know that we could both be on one
    But if somebody try to start some
    I’m gon’ try for you
    I’ll fight for you, go off for you
    I’ll start a war
    Ever since the day we locked in
    I was gonna be a down bitch
    If I need to start a war
    I’m gon’ try for you
    I’ll fight for you, go off for you
    I’ll start a war
    Yeah, yeah
    You know I’ll start a war
    Yeah, yeah
    You know I’ll start a war
    Yeah
    You know I’ll start a war
    Yeah, yeah
    You know I’ll start a war'
);

SET @lyrics_track_4 = CONCAT_WS('\n',
    'I trip and fall in love
    Just like a Tuesday drunk
    I always go all in, all in, all in
    Over the handlebars
    Hitting the ground so hard
    If I’m alone, fallin’, fallin’, fallin’
    We ain’t gotta talk about it
    Mercy
    Why is it love is never kind to me?
    I heard that fools rush in and, yeah, that’s me
    It burns me time and time again
    So why am I still fixing for this frying pan, thinkin’
    I wonder what you’re doing for tonight and forever (oh-oh)
    I could be the rest of your life or whatever
    My lips and your lips, we could press them together (’gether, ’gether, ’gether)
    I don’t ever think twice, and, baby, that’s why
    I trip and fall in love
    Just like a Tuesday drunk
    I always go all in, all in, all in
    Over the handlebars
    Hitting the ground so hard
    If I’m alone, fallin’, fallin’, fallin’
    Another round, another drink
    I try to stop, but I can’t think
    About anything else but you (but you)
    And I’m a little too buzzed on your love to play it cute
    A single kiss, I lost my mind for seven days and seven nights
    Can’t eat, sleep, baby, it’s true (it’s true)
    Tryna bite my lip, I’m probably gonna slip
    And say some crazy things to you
    I wonder what you’re doing for tonight and forever (oh-oh)
    I don’t ever think twice, and maybe that’s why
    I trip and fall in love
    Just like a Tuesday drunk
    I always go all in, all in (all in, all in), all in
    Over the handlebars
    Hitting the ground so hard
    If I’m alone, fallin’, fallin’, fallin’ (fallin’, yeah)
    We ain’t gotta talk about it
    Na-na-na-na-na-na, na (yeah)
    We ain’t gotta talk about it
    Na-na-na-na-na-na, na
    We ain’t gotta talk about it'
);

SET @lyrics_track_5 = CONCAT_WS('\n',
    'are you? Are you?
    (Ah, uh, ah, uh) party in the back room
    (Ah, uh, ah, uh) I done left it in the restroom (incomin’)
    (Ah, uh, ah, uh) now my attitude is yeah, yeah, yeah
    Way up, all the way up
    Shimmy, shimmy, yeah, I’ma let it go
    Shots fire on my way up
    Bulletproof glass when I’m ridin’ through
    Way up, all the way up
    Gimme, gimme that, I won’t let it go
    Shots fire on my way up
    Bulletproof glass when I’m ridin’ through
    No more cycles on your merry-go
    Straight line’s a hate crime, villain in a scary coat
    Your fuckin’ sea of judgment, watch her, there she floats
    Nasty, flashy, wave-choppin’ motor-boat
    Target on my name, but your aim’s way off
    Why are you evaluatin’ me on your day off?
    Set a fire now, said I want it now, uh-huh
    Spectators ’round hear the siren sound
    Way up, all the way up
    Shimmy, shimmy, yeah, I’ma let it go
    Shots fire on my way up
    Bulletproof glass when I’m ridin’ through
    Way up, all the way up
    Gimme, gimme that, I won’t let it go
    Shots fire on my way up
    Bulletproof glass when I’m ridin’ through
    Rooftop when I party, turnt like a Harley
    Sorry not sorry, yeah
    Shadows all around me, close and they crowd me
    Breathe, I can hardly (ah)
    It seems I got a chokehold on ’em
    Everybody’s cool, but when I do it I’m the problem
    Gave you too much and it’s givin’ spoiled rotten
    Got me stressed out bein’ the trendin’ topic
    Yeah, yeah, yeah, yeah, yeah, yeah, yeah, yeah (yeah, yeah, watch me)
    Why a killer never looked so sweet?
    Yeah, yeah, yeah, yeah, yeah, yeah, yeah, yeah (I’m so, set a fire now, set ’em all off, uh-huh)
    Yeah, yeah, yeah, yeah, yeah, yeah, yeah, yeah (spectators ’round hear the siren sound)
    I’m hot cold, gelato
    An angel, diablo
    I’m on one, I’m calm though
    Come, give me a kiss
    Get up out my face, yeah, yeah, yeah
    are you? Are you?
    (Ah, uh, ah, uh) party in the back room
    (Ah, uh, ah, uh) I done left you in the restroom
    (Ah, uh, ah, uh) now my attitude is yeah, yeah, yeah
    Way up, all the way up
    Shimmy, shimmy, yeah, I’ma let it go
    Shots fire on my way up
    Bulletproof glass when I’m ridin’ through
    Way up, all the way up (yeah, yeah, yeah, yeah, yeah, yeah, yeah, yeah)
    Gimme, gimme that, I won’t let it go (yeah, yeah, yeah, yeah, yeah, yeah, yeah, yeah)
    Shots fire on my way up (yeah, yeah, yeah, yeah, yeah, yeah, yeah, yeah)
    Bulletproof glass when I’m ridin’ through
    Yeah, yeah, ah
    Set a fire now, said I want it now, uh-huh
    Spectators ’round hear the siren sound'
);

SET @lyrics_track_6 = CONCAT_WS('\n',
    'Do my, do my ladies run this, ladies run this?
    Do my, do my ladies run this, ladies run this? (Yeah)
    Do my, do my ladies run this, ladies run this? (Incoming)
    Do my, do my ladies run this, ladies run this? (Yeah, yeah, yeah, yeah)
    All of my girls looking good and they got they own money (do my, do my ladies run this?)
    Pop your shit
    This for my girls with no sponsor, they got they own fundin’ (do my, do my ladies run this?)
    Not your shit
    Run through your city, that motorcade (do my, do my ladies run this?)
    Soon as I enter, they close the gate (ladies run this?)
    Presidential through your residential
    Bitch, it’s nothing
    Said, "Fuck your rules, " is the mood, damn right
    Walk in a room and I set the vibe
    Get a pic, it’ll last you long
    Whole team, they gassin’ on us
    You sit too far down on ’em charts to even ask me who’s in charge
    Ridin’ ’round, foreign cars (yeah)
    Top down, starin’ at the stars (yeah)
    Attitude, so don’t start shit (yeah)
    Big moves, only extra large, yeah
    Ridin’ ’round, foreign cars
    Top down, starin’ at the stars (yeah)
    Attitude, so don’t start shit
    Big moves, only extra large, yeah
    Wait (do my ladies run this?)
    Wait (do my ladies run this?)
    Wait (do my ladies run this?)
    Doechii (yo, yeah)
    Gimme chi, gimme purr, gimme meow, gimme her, gimme funds
    Gimme rights, gimme fight, gimme nerve, gimme cunt, let me serve, rrr
    Lemme, lemme out, lemme in
    Knock the doors down, got the keys to the Benz
    In the boardroom looking bored ’cause I’m not here for pleasin’ the men
    Not here to reason with them
    Misbehaved, Miss Push-My-Pen
    I can’t tame my passion for him
    Can’t keep up, what happened to them? (Do my ladies run this?)
    Yeah, we lappin’ the men
    Top of the food chain, bussin’ a new chain
    This ain’t a new thing, no, sir
    Money on stupid, hopped in a new whip
    You still on my old work (yeah, yeah)
    Work, work, this might hurt (yeah, yeah)
    I sweat hard, wet T-shirt (yeah, yeah)
    Extra large, ain’t scared of the dirt (yeah, yeah)
    Hit that jackpot, now I’m
    Ridin’ ’round (ridin’ ’round), foreign cars (foreign cars)
    Top down (top down), starin’ at the stars (yeah)
    Attitude (attitude), so don’t start shit (so, don’t start shit)
    Big moves, only extra large, yeah (big, big, big, big)
    Ridin’ ’round (ridin’ ’round), foreign cars (foreign cars)
    (Do my, do my ladies run this, ladies run this?)
    Top down (top down), starin’ at the stars (yeah)
    (Do my, do my ladies run this, ladies run this?)
    Attitude (attitude), so don’t start shit (so don’t start shit)
    (Do my, do my ladies run this, ladies run this?)
    Big moves, only extra large, yeah (big, big, big, big)
    (Do my, do my ladies run this, ladies run this?)
    Work, work, this might hurt
    I sweat hard, wet T-shirt
    Extra large, ain’t scared of the dirt (scared of the dirt), yeah, yeah
    Work, work, this might hurt
    I sweat hard, wet T-shirt (yeah, yeah)
    Extra large, ain’t scared of the dirt (yeah, yeah) (scared of the dirt)
    Work, work (rrr)
    Do my, do my ladies run this, ladies run this?
    Do my, do my ladies run this, ladies run this?
    Do my, do my ladies run this, ladies run this?
    Do my, do my ladies run this, ladies run this?'
);

SET @lyrics_track_7 = CONCAT_WS('\n',
    'Pretty, pretty, pretty, pretty
    This that pretty-girl mantra, this that flaunt you
    Just touched down in L.A.
    Pretty girls don’t do drama, ’less we wanna
    It’ll be depending on the day
    Pretty girls packed in a Defender, know I’ma defend her
    Never let her catch no stray
    This that pretty-girl mantra, she’s that stunna
    Make you wanna swing both ways
    Mix me with the drama (drama)
    Check you like commas (ah)
    My clothes are pajamas (’jamas)
    Straight from the cold plunge (hey) (ah)
    Daytime baddie use her mind
    Quick switch of the fit for the night (night)
    Swerving through the lane, we’ll be twenty-minute-late
    ’Cause we had to do an In-N-Out drive-by
    It’s not that deep (deep), I’m not that drunk (drunk)
    Sometimes girls just gotta have fun
    Throw it back, all that ass
    Me and my sis, way too attached
    It’s not that deep (deep), we’re not that dumb (dumb)
    Look at them Bonnies on the run
    Inside glowing like the sun (sun, s-)
    You gonna feel us every day (day)
    This that pretty-girl mantra, this that flaunt you
    Just touched down in L.A.
    Pretty girls don’t do drama, ’less we wanna
    It’ll be depending on the day
    Pretty girls packed in a Defender, know I’ma defend her
    Never let her catch no stray
    This that pretty-girl mantra, she’s that stunna
    Make you wanna swing both ways
    Love what it feel like (feel like)
    To be off of the grid, like, all night
    Oh, with my bih like (bitch, like)
    We ain’t even tryna talk to no one
    Swerve off all the creeps, no weird vibes
    We ain’t never let it ruin a good time
    Ain’t nobody gon’ dim our good light
    This them words we’re living by
    This that pretty-girl mantra, this that flaunt you
    Just touched down in L.A. (ah)
    Pretty girls don’t do drama, ’less we wanna
    It’ll be depending on the day (ah, ah, ah)
    Pretty girls packed in a Defender, know I’ma defend her
    Never let her catch no stray (ah, ah)
    This that pretty-girl mantra, she’s that stunna
    Make you wanna swing both ways (ah, ah)
    This that pretty-girl mantra, this that flaunt you
    Just touched down in L.A. (ah, ah)
    Pretty girls don’t do drama, no new drama
    We already got a full day (ah, ah)
    Pretty girls that you gon’ remember, know that you could never
    Nothing ever trigger me (ah, ah)
    This that pretty-girl mantra, she’s that stunna
    Everyone know that she is me (ah)
    Pretty'
);

SET @lyrics_track_8 = CONCAT_WS('\n',
    'I’m over, I’m so over
    This love hangover
    Fight me, fight me, fight me
    You made me so unlike me
    I don’t wanna talk, come behind me
    Know you ain’t the one, but you might be
    Who sent you? Who sent you?
    Who sent you? Who sent you ’round again?
    I’m so, I’m so shady
    I don’t really mind when you play me
    Wanna switch it up, go crazy
    I ain’t gonna leave ’til you hate me
    Who sent you? Who sent you?
    Who sent you? Who sent you ’round?
    We say it’s over, but I keep fucking with you (yeah)
    And every time I do, I wake up with this love hangover
    You got me pouring for two, I swore I’d never do it again
    Until you came over, I started lying with you (yeah)
    And every time I do, I wake up with this love hangover
    Ah, oh, I swear I’ll never do it again
    Ah, shit, I did it again (call me back, call me back, call me back)
    Oh, but you know I’m gonna do it again
    (Oh, shit, oh, shit, call me back, call me back, call me back)
    Yeah, you know I’m gonna do it again
    I had woke up in a daze, my sweat was cold, my lip was cracked
    I can’t leave this bitch, I had to single, double, triple back
    She gon’ leave me, but she wants to keep me on, what’s up with that?
    I don’t even really got time for all that shit right now, I’m a baby father
    And all them jokes she told at dinner last night
    Ain’t had me dead, I was playing possum
    And when the waiter brought the check
    She said, "Let’s head to mine, " I said, "Okay, awesome"
    One minute, we’re growing apart, and next I’m in her apartment
    Just watching her get naked and not thinking with my heart
    I ain’t even really got time for all that shit right now (right now)
    But if she wanted it right now (right now)
    Then I could meet you there right now (right now)
    Even though you barely even drink (uh-huh)
    We hardly even spoke (uh-huh)
    But I know when I wake up that I’m still gon’ feel that hangover, babe
    We say it’s over, but I keep fucking with you (yeah)
    And every time I do, I wake up with this love hangover
    You got me pouring for two, I swore I’d never do it again
    Until you came over, I started lying with you (yeah)
    And every time I do, I wake up with this love hangover
    Ah, oh, I swear I’ll never do it again
    Ah, shit, I did it again (call me back, call me back, call me back)
    Oh, but you know I’m gonna do it again (oh, shit)
    (Call me back, call me back, call me back, uh-huh)
    Yeah, you know I’m gonna do it again
    Back, back, back, back, back
    (Call me back, call me back, call me back)
    Back, back, back, back, back (ah, shit, ah, shit, ay)
    Back, back, back, back, back
    (Call me back, call me back, call me back)
    Back, back, back, back, back (ah, shit, ah, shit, ay)
    Back, back, back, back, back, single, double, triple back
    (Call me back, call me back, call me back, uh-huh)
    Back, back, back, back, back, single, double, triple back right now, right now (yeah)
    (Call me back, call me back, call me back)
    Back, back, back, back, back (ah, shit, ah, shit)
    (Call me back, call me back) single, double, triple back
    Back, back, back, back, back (uh-huh)
    Don’t know what I’m saying at this point'
);

SET @lyrics_track_9 = CONCAT_WS('\n',
    'I tell ’em, "Down, now"
    On that energy, yes
    I am what you think about me
    Cross me, please
    I’ma keep it Z, Zen
    Presence, bless
    Money can’t buy sixth sense
    Bad bitch, ’kay, so make me better
    Fire aura quiets chatter
    Shoo, shoo, shoo, I make ’em scatter
    They can’t move my matter
    Nobody gon’ move my soul, gon’ move my aura, my matter
    Nobody gon’ move my light, gon’ touch my glow, my matter
    Nobody gon’-, all this power make them scatter
    No, nobody gon’ touch my soul, gon’ match my glow, like
    I dare you (hey)
    shake me
    (Ah, ah) hey
    Thick skin layered like chains on chains on chains
    Wear the pressure on my neck and rings
    Rain, midnight bloom
    In the dark, I grew
    Shoo, shoo, shoo, shoo, shoo, shoo, freeze
    Shoo, shoo, shoo, shoo, shoo, shoo, gleam
    Shoo, shoo, shoo, shoo, shoo, shoo (one hunnid, one hunnid), ten
    Shoo, shoo, shoo, shoo (one hunnid), money cannot buy no real friends
    Baddest, they can’t make me badder
    Fire aura quiets chatter
    Shoo, shoo, shoo, I make ’em scatter
    They can’t move my matter
    Nobody gon’ move my soul, gon’ move my aura, my matter
    Nobody gon’ move my light, gon’ touch my glow, my matter
    Nobody gon’, all this power make them scatter
    No, nobody gon’ touch my soul, gon’ match my glow, like
    I dare you (hey)
    shake me
    (Ah, ah) hey
    (Ah, ah)
    (Ah, ah) can’t be two of one'
);

SET @lyrics_track_10 = CONCAT_WS('\n',
    'Uh-uh
    Popped up on you solo on my lonely shit
    You didn’t even know the type time I was on
    Told ya, "Hop in on the left side", rock the ship
    Now you’re struggling to keep your eyes on the road
    And you saw me whip my hair in the wind playing Beyoncé
    Putting that good work in like a fiancé
    Finish line was gold, better go ahead and lend me them keys to the condo
    I’m like
    Damn, right, I did that
    Damn, right, yeah (ooh-ooh-ooh)
    Damn, right, I did that
    Yeah, I did (ooh-ooh-ooh)
    Damn, right, I did that
    Damn, right, yeah (ooh-ooh-ooh)
    Damn, right, I did that
    Yeah, I did (ooh-ooh-ooh, yeah)
    Damn, I look so pretty when I’m overseas
    I introduce you to the finer things
    When I put it down like how I want my body
    Let me do my thing, make you hear the angels sing
    ’Cause I do it so effortlessly, do it my way
    Do it so good, I’ll make your troubles disappear
    Damn, I do it so well, make the time stand still
    Gotta give myself tens when they’re clearly due
    Like
    Damn, right, I did that (yes, I did)
    Damn, right, yeah (I did)
    Damn, right, I did that
    Yeah, I did
    Damn, right, I did that (yes, I did)
    Damn, right, yeah (I did)
    Damn, right, I did that
    Yeah, I did
    Damn, right
    Can I be the only one? (Oh-oh)
    You feel good to me (yes, you do, yes, you do)
    You know it (you know it)
    You know it, you know it, mm
    Damn, right, yeah, I’m dreamin’ ’bout your body, all night (ooh-ooh), yeah
    I been with models, they was alright, yeah (they was alright)
    But they ain’t you
    Candy-cane blue sticks bump in the Range (you make me feel so good)
    Gettin’ top notch means the simpler things
    Playin’ hopscotch but she landed a square (you make me feel so good)
    He never even tried to put her legs in the air (ooh-ooh)
    He never even tried to put a baby in that
    No matter who you racin’ when you jump in the set (you make me feel so good)
    Just know it’s gonna come back (ooh-ooh)
    A lot of niggas thought that they was workin’ (you make me feel so good)
    But she laughing ’bout your stroke in a chat (ooh-ooh)
    The confidence lack
    They used to have to talk but now they look at the watch
    The chain ain’t a thang let me look at them stocks (ooh-ooh)
    I walk around Atlanta like I live in a box (you feel so good)
    She pop a red balloon and now he kickin’ the rocks
    You playin’ with fire
    I said she was the sweetest ’til she made me a liar
    I used to work the middle but I had to retire (you make me feel so good)
    She did me something dirty but she did it with style, damn, right
    Damn, right, I did that (you make me feel so good)
    Damn, right, yeah
    Damn, right, I did that (you make me feel so good)
    Yeah, I did
    Damn, right, I did that (you make me feel so good)
    Damn, right, yeah
    Damn, right, I did that (you make me feel so good)
    Yeah, I did
    Damn, right (I did, I did, I did, I did)
    Damn, right, yeah
    Damn, right, I did that (yes, I did)
    Yeah, I did
    Damn, right (I did, I did, I did, I did)
    Damn, right, yeah (yes, I did)
    Damn, right, I did that, oh (yes, I did)
    Yeah, I did
    All night
    Ta-da-di-da-day
    Yeah, I did that
    Yeah, I did that
    Yeah, I did that'
);

SET @lyrics_track_11 = CONCAT_WS('\n',
    'Maybe it’s time to take a leap of faith (ah-ah, ah-ah)
    And come to my senses and take my shirt off in the rain (ah-ah, ah-ah)
    Strike a fuckin’ match of love and desire and warm my hands up in the flame
    Whatever happened to freedom and honesty? (Ooh)
    What matters to you, you, you, it’s not that deep to me
    Fuck that shit, ah, yeah
    Flip the script, ah, yeah
    Inside of me, ah, ooh
    Ooh, ooh, ooh, ooh
    Fuck that shit, I am
    Over it, ah, yeah
    Off the grid, ah, ooh
    Ooh, ooh, ooh, ooh (fuck that shit)
    I’m in love, you’re on game
    Switchin’ up, switchin’ lanes
    Won’t fight the urge, I’ll go insane
    I’ll say what I want if this shit’s true (true)
    Oh, yeah, if that shit’s true (if that shit’s true)
    Whatever happened to freedom and honesty?
    What matters to you, you, you, it’s not that deep to me
    Fuck that shit, ah, yeah
    Flip the script, ah, yeah
    Inside of me, ah, ooh
    Ooh, ooh, ooh, ooh
    Fuck that shit, I am
    Over it, ah, yeah
    Off the grid, ah, ooh
    Ooh, ooh, ooh, ooh (fuck that shit)'
);

SET @lyrics_track_12 = CONCAT_WS('\n',
    'Incomin’ (la-la-la-la)
    I woke up like this, feelin’ like a weight just lifted
    I don’t know what it is, but I swear to God I love this shit
    Look in the mirror, there ain’t nothin’ clearer
    So take off your filter, bitch
    What you gon’ do with that? (Yeah, yeah)
    Anything I want is in my reach, yeah, I like that (yeah)
    Unapologetic when I creep, yeah, it’s like that (yeah)
    All the flashing lights, they follow me, yeah, I like that
    (Yeah-yeah, yeah-yeah-yeah, yeah)
    Full throttle crashin’ through the gate when I ride out (yeah)
    Quick to judge a book by the front, inside out (yeah)
    Never cared what you thought then, why should I now? (Yeah)
    (Yeah-yeah, yeah-yeah-yeah, yeah)
    Undress me on the way to perfection, yeah
    Underneath, finally found what’s been missin’
    When I take it off
    I know I love me more
    With no filter, filter, oh
    With no filter, filter, oh
    With no filter, uncensored
    When I take it all off, I love me more
    With no filter (la-la-la-la)
    I found it under it all
    Simple and so beautiful
    Go ’head and judge me
    Nothin’ can touch me when I take it off
    Undress me (undress me) on the way to perfection, yeah
    Underneath (underneath), finally found what’s been missin’
    When I take it off
    I know I love me more
    With no filter (oh)
    (Filter) oh, with no filter (filter)
    With no filter, filter (oh)
    With no filter, filter
    Oh, with no filter, uncensored
    When I take it all off, I love me more
    With no filter'
    );

SET @lyrics_track_13 = CONCAT_WS('\n',
    'Ooh
    Ooh
    Ooh
    (Mike WiLL Made-It)
    Give me hug, need your love, touch my thigh
    Tell me what puts you in that mind
    Frame it up, draw me in, do me right
    Don’t you dare leave my sight
    I could be, be your prize, pick me up
    Flying lights, paradise
    In Seoul city
    I see your soul
    Seoul city
    I see your soul
    Yeah, yeah
    Hey, ayy, hey
    +82, some miracle
    Only listen to my general, whoa
    He says my attitude out of control
    Tell me what to do, Mr. General
    Oh-oh
    Would you make me your boss, pretty please?
    Pretty please, let me ease your mind
    Look at me, can you breathe? (Ah, ah)
    I could give you life
    Apple of, of my eye, pick me up
    Flying lights, paradise
    In Seoul city
    I see your soul
    Seoul city
    I see your soul
    Yeah, yeah
    Hey, ayy, hey
    +82, some miracle
    Only listen to my general, whoa
    He says my attitude out of control
    Tell me what to do, Mr. General
    Oh-oh'
);

SET @lyrics_track_14 = CONCAT_WS('\n',
    '저긴 어딜까?
    저 별의 시작과 끝은 어디일까?
    나도 모르겠어
    그 사이 어딘가쯤에 있지 않을까?
    You say you see the starlight in me
    Shining so bright and pristine
    What about the moments in between?
    You said you see the starlight in me
    What about the black mystery?
    What about the moments you don’t see?
    It’s way deeper than what you think
    I’m tired of that Novocain
    Put all that shit away (away)
    I wanna feel everything
    I was just a white, white, white, lie, lie
    Truth comes out in time, time, time, every time
    I know where my soul has been
    Now I remember the night
    Remember the night
    Now I remember thе night
    Remember thе night
    Yeah, yeah, yeah, yeah, yeah, yeah, yeah, yeah
    Starlight bright, starlight bright, starlight bright, starlight
    Yeah, yeah, yeah, yeah, yeah, yeah, yeah, yeah
    Starlight bright, starlight bright, starlight bright, starlight
    So many after hours
    I just wanna make my mama prouder
    When the stupid thoughts started getting louder
    Said, "Bitch, chill out, " and took a cold shower
    Like we gon’ levitate, gon’ levitate
    To the 808, I gravitate to the real, not fake
    And this time, it’s on me
    ’Cause I remember the night
    Remember the night
    Now I remember the night
    Remember the night
    Yeah, yeah, yeah, yeah, yeah, yeah, yeah, yeah
    Starlight bright, starlight bright, starlight bright, starlight
    Yeah, yeah, yeah, yeah, yeah, yeah, yeah, yeah
    Starlight bright, starlight bright, starlight bright, starlight
    Starlight bright, starlight bright, starlight bright, starlight
    Starlight bright, starlight bright, starlight bright, starlight
    저기 반짝이는 별처럼
    내 꿈속에서 점점 가까워지는 거 아닌가?'
);

SET @lyrics_track_15 = CONCAT_WS('\n',
    'It’s like I’m writing a letter
    And I put in a twelve-ounce bottle of Heineken
    In the Atlantic on a whim
    ’Cause I know I’ve been gone too long
    But I’m writing a song
    It’s like I’m writing a letter, but I’m writing a song
    It’s like I’m writing a letter, but I’m writing a song
    It’s like I’m writing a letter, but I’m writing a song
    Can you just bear with me? We were ten years in
    And young and dumb and innocent, my friend
    But I knew all along that we were both wrong
    It’s like I’m writing a letter, but I’m writing a song
    It’s like I’m writing a letter, but I’m writing a song
    It’s like I’m writing a letter, but I’m writing a song
    I didn’t leave ya, I still see ya
    When I’m bumping Ashanti, yeah, on a beach, yeah
    I didn’t hold ya, but I still know ya
    We will make up, make things right when we get older, friend
    Twin, twin, twin
    You and I, we drifted apart
    Twin, twin, twin
    Like the white clouds under the stars
    Do you feel a way?
    I blamed the timing, wasn’t timing
    We was fighting and colliding, man, I just couldn’t stay
    And I keep your name so, so, so tightly to my heartbeat
    Guess I lost you and you lost me, but I put fuel to your flame
    I didn’t leave ya, I still see ya
    When I’m bumping Ashanti, yeah, on a beach, yeah
    I didn’t hold ya, but I still know ya
    We will make up, make things right when we get older, friend
    Twin, twin, twin
    You and I, we drifted apart
    Twin, twin, twin
    Like the white clouds under the stars
    Twin, twin, twin
    You and I, we drifted apart
    Twin, twin, twin'
);

UPDATE `track`
SET `lyrics` = CASE `id`
    WHEN 1 THEN @lyrics_track_1
    WHEN 2 THEN @lyrics_track_2
    WHEN 3 THEN @lyrics_track_3
    WHEN 4 THEN @lyrics_track_4
    WHEN 5 THEN @lyrics_track_5
    WHEN 6 THEN @lyrics_track_6
    WHEN 7 THEN @lyrics_track_7
    WHEN 8 THEN @lyrics_track_8
    WHEN 9 THEN @lyrics_track_9
    WHEN 10 THEN @lyrics_track_10
    WHEN 11 THEN @lyrics_track_11
    WHEN 12 THEN @lyrics_track_12
    WHEN 13 THEN @lyrics_track_13
    WHEN 14 THEN @lyrics_track_14
    WHEN 15 THEN @lyrics_track_15
    ELSE `lyrics`
END
WHERE `id` BETWEEN 1 AND 15;
