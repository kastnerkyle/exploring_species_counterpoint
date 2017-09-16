# -*- coding: utf-8 -*-
from __future__ import print_function
import subprocess
from music21 import converter, roman, key
import os
import numpy as np
import fractions

# https://github.com/davidnalesnik/lilypond-roman-numeral-tool
# http://lsr.di.unimi.it/LSR/Snippet?id=710
roman_include = r"""
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% A function to create Roman numerals for harmonic analysis.
%%
%% Syntax: \markup \rN { ...list of symbols... }
%%
%% List symbols in this order (as needed): Roman numeral (or note name),
%% quality, inversion figures from top to bottom, "/" (if a secondary
%% function), Roman numeral (or note name).  Usually, you can skip unnecessary
%% items, though a spacer may be needed in some cases.  Use "" instead of the
%% initial symbol to start with the quality or inversion, for example.  Elements
%% must be separated by whitespace.
%%
%% Notenames are represented by their English LilyPond names.  In addition, you
%% may capitalize the name for a capitalized note name.
%%
%% Preceding a string representing a Roman numeral with English alterations
%% (f, flat, s, sharp, ff, flatflat, ss, x, sharpsharp, natural)
%% will attach accidentals, for example, "fVII" -> flat VII; "sharpvi" -> sharp vi.
%% You may precede inversion numbers with alterations, though "+" is not
%% presently supported.
%%
%% Qualities: use "o" for diminished, "h" for half-diminished, "+" for augmented,
%% and "f" for flat.  Other indications are possible such as combinations of "M"
%% and "m" (M, m, MM7, Mm, mm, Mmm9, etc.); add, add6, etc.
%%
%% To scale all numerals: \override  LyricText #'font-size = #2
%% or \override  TextScript #'font-size = #2
%% To scale individual numerals: \markup \override #'(font-size . 2) \rN { ... }
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% THE APPROACH %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%% In our approach, a Roman numeral consists of

%% 1. A "base".  OPTIONAL. This may be a Roman numeral (some combination of I, i, V,
%% and v, unenforced); a note name; or some other string.  Roman numerals may be
%% preceded by an accidental, and a note name may be followed by one.

%% 2. a quality indicator.  OPTIONAL.  Eventually, this will simply be something to
%% set as a superscript following the base, whether or not it is actually a
%% indicator of quality.

%% 3. A single inversion number, or more than one, to be set as a column.  OPTIONAL.
%% An initial accidental is supported.  (This will be extended to "anything you want
%% to appear in a column after the quality indicator.")

%% 4. "/" followed by a "secondary base" for indicating tonicization.  OPTIONAL.
%% As with 1. this may a Roman numeral or note name, and may include an accidental.

%% The input syntax is chosen to be friendly to the user rather than the computer.
%% In particular, the user usually need only type the symbols needed when
%% reading the analytical symbol aloud.  This is not perfect: spacers
%% may be necessary for omissions.  Additionally, we try to interpret symbols
%% without requiring extra semantic indicators: i.e., figure out whether a string
%% represents a Roman numeral or a note name without the user adding an extra sign.
%% In the future, indicators might prove necessary to resolve ambiguity: along with
%% a flag to distinguish Roman numeral from note name, braces to enclose inversion
%% figures may be useful.

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% INPUT FORMATTING %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%% The user's input is available as a list of strings.  Here we convert this
%% list into a nested list which describes the structure of the input.

#(define (split-list symbols splitter-list)
   "Split a list of strings by a splitter which is a member of a list of
potential splitters.  The splitter may be alone or part of a string.
input is split into
@code{(( ...strings up to splitter... ) ( ...strings beginning with splitter... ))}
This function is Used to split notation for secondary chords and to isolate
inversion numbers."
   (let loop ((sym symbols) (result '()))
     (cond
      ((or (null? sym)
           (find (lambda (y) (string-contains (car sym) y)) splitter-list))
       (list (reverse result) sym))
      (else (loop (cdr sym) (cons (car sym) result))))))

#(define numbers '("2" "3" "4" "5" "6" "7" "8" "9" "11" "13"))

#(define qualities
   ;; only to allow omission of base when quality is alone
   ;; TODO--combinations of M and m, add, ADD . . .
   '("o" "+" "h"))

#(define (base-and-quality arg)
   (let ((len (length arg)))
     (cond
      ((= 0 len) '(() ()))
      ((= 1 len)
       (if (find (lambda (y) (string= (car arg) y)) qualities)
           (list '() (list (car arg)))
           (list (list (car arg)) '()))) ;; TODO figure out which is given
      ((= 2 len) (list (list (car arg)) (cdr arg))))))

#(define (base-quality-figures symbols)
   ;; given (vii o 4 3) --> ((vii o) (4 3)) --> ((vii) (o) (4 3))
   ;; (4 3) --> (() (4 3)) --> (() () (4 3))
   ;; () --> (() ()) --> (() () ())
   (let* ((split-by-numbers (split-list symbols numbers))
          (b-and-q (base-and-quality (car split-by-numbers))))
     (append b-and-q (cdr split-by-numbers))))

#(define (parse-input input)
   (let (;; (vii o 4 3 / ii) --> ((vii o 4 3) (/ ii))
          (split (split-list input '("/"))))
     ;; --> ( ((vii) (o) (4 3)) (/ ii) )
     (append
      (list (base-quality-figures (car split)))
      (cdr split))))

%%%%%%%%%%%%%%%%%%%%%%%%%%%% NOTE NAMES / ACCIDENTALS %%%%%%%%%%%%%%%%%%%%%%%%%%

%% Formatting the input into interpretable lists continues here.  We are now
%% concerned with distinguishing Roman numerals from note names, and with representing
%% the presence and position of accidentals.

%% If a string belongs to the list of possible English notenames, we assume that
%% it is a note name.  The note name will be typeset as uppercase or lowercase depending
%% on the capitalization of the input string.

%% If a string is not a note name, we look for an alteration prefix, never a suffix.

%% The procedure parse-string-with-accidental breaks a string into a list representing
%% initial/terminal alterations and what is left.

%% Notenames and names of accidentals are based on English names.  Other
%% languages may be used by adding variables modeled after english-note names and
%% english-alterations, and changing the definitions of note names and alterations to
%% point to these new variables.

#(define english-note-names
   (map (lambda (p) (symbol->string (car p)))
     (assoc-get 'english language-pitch-names)))

#(define note-names english-note-names)

#(define (note-name? str)
   (let ((lowercased (format #f "~(~a~)" str)))
     (list? (member lowercased note-names))))

%% Groupings sharing an initial character are arranged in descending length so there
%% is no need to search for longest match in parse-string-with-accidental.
#(define english-alterations
   '("flatflat" "flat" "ff" "f"
      "sharpsharp" "sharp" "ss" "s" "x"
      "natural" "n"))

#(define alterations english-alterations)

#(define (parse-note-name str)
   "Given a note name, return a list consisting of the general name followed by
the alteration or @code{#f} if none."
   (let* ((first-char (string-take str 1))
          (all-but-first (string-drop str 1))
          (all-but-first (if (string-prefix? "-" all-but-first)
                             (string-drop all-but-first 1)
                             all-but-first))
          (all-but-first (if (string-null? all-but-first) #f all-but-first)))
     (list first-char all-but-first)))

#(define (parse-string-with-accidental str)
   "Given @var{str}, return a list in this format: (initial-accidental?
note-name-or-figure-or-RN terminal-accidental?) If an accidental is found, include
its string, otherwise @code{#t}."
   (if (not (string-null? str))
       (if (note-name? str)
           (cons #f (parse-note-name str))
           ;; Is it a Roman numeral or figure preceded (or followed) by an accidental?
           (let* ((accidental-prefix
                   (find (lambda (s) (string-prefix? s str)) alterations))
                  (accidental-suffix
                   (find (lambda (s) (string-suffix? s str)) alterations))
                  (rest (cond
                         (accidental-prefix
                          (string-drop str (string-length accidental-prefix)))
                         (accidental-suffix
                          (string-drop-right str (string-length accidental-suffix)))
                         (else str))))
             (list accidental-prefix rest accidental-suffix)))))
%{
#(define (inversion? str)
   "Check to see if a string contains a digit.  If so, it is an inversion figure."
   (not (char-set=
         char-set:empty
         (char-set-intersection (string->char-set str) char-set:digit))))
%}

%% We need to add extra space after certain characters in the default LilyPond
%% font to avoid overlaps with characters that follow.  Several of these kernings
%% don't seem to be necessary anymore, and have been commented out.
#(define (get-extra-kerning arg)
   (let ((last-char (string-take-right arg 1)))
     (cond
      ((string= last-char "V") 0.1)
      ((string= last-char "f") 0.2)
      ;((string= last-char "s") 0.2) ; sharp
      ;((string= last-char "x") 0.2) ; double-sharp
      ;((string= last-char "ss") 0.2) ; double-sharp
      (else 0.0))))

%% Create accidentals with appropriate vertical positioning.
#(define make-accidental-markup
   `(("f" . ,(make-general-align-markup Y DOWN (make-flat-markup)))
     ("flat" . ,(make-general-align-markup Y DOWN (make-flat-markup)))
     ("ff" . ,(make-general-align-markup Y DOWN (make-doubleflat-markup)))
     ("flatflat" . ,(make-general-align-markup Y DOWN (make-doubleflat-markup)))
     ("s" . ,(make-general-align-markup Y -0.6 (make-sharp-markup)))
     ("sharp" . ,(make-general-align-markup Y -0.6 (make-sharp-markup)))
     ("ss" . ,(make-general-align-markup Y DOWN (make-doublesharp-markup)))
     ("x" . ,(make-general-align-markup Y DOWN (make-doublesharp-markup)))
     ("sharpsharp" . ,(make-general-align-markup Y DOWN (make-doublesharp-markup)))
     ("n" . ,(make-general-align-markup Y -0.6 (make-natural-markup)))
     ("natural" . ,(make-general-align-markup Y -0.6 (make-natural-markup)))))

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% BASE MARKUP %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

#(define (make-base-markup base scaling-factor)
   (let* ((base-list (parse-string-with-accidental base))
          (init-acc (first base-list))
          (end-acc (last base-list))
          (extra-space-right (get-extra-kerning (second base-list))))
     (cond
      (init-acc
       (make-concat-markup
        (list
         (make-fontsize-markup -3
           (assoc-ref make-accidental-markup init-acc))
         (make-hspace-markup (* 0.2 scaling-factor))
         (second base-list))))
      (end-acc
       (make-concat-markup
        (list
         (second base-list)
         (make-hspace-markup (* (+ 0.2 extra-space-right) scaling-factor))
         (make-fontsize-markup -3
           (assoc-ref make-accidental-markup end-acc)))))
      (else
       (if (> extra-space-right 0.0)
           (make-concat-markup
            (list
             base
             (make-hspace-markup (* extra-space-right scaling-factor))))
           base)))))

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% QUALITY %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%% Symbols representing diminished, half-diminished, and augmented qualities are
%% drawn to rest atop of baseline (alignment direction = DOWN), and moved by
%% make-quality-markup to their final vertical position.  They are tailored to
%% the font-size (-3) of the ultimate caller (\rN -- default font-size = 1).

%% These symbols are drawn from scratch to allow for customization.  should we
%% simply use symbols from a font?

#(define (make-diminished-markup font-size)
   "Create circle markup for diminished quality."
   (let* ((scaling-factor (magstep font-size))
          (r (* 0.48 scaling-factor))
          (th (* 0.1 scaling-factor)))
     (make-translate-markup
      (cons r r)
      (make-draw-circle-markup r th #f))))

#(define (make-half-diminished-markup font-size)
   "Create slashed circle markup for half-diminished quality."
   (let* ((scaling-factor (magstep font-size))
          (x (* 0.56 scaling-factor))
          (y (* 0.56 scaling-factor))
          (r (* 0.48 scaling-factor))
          (th (* 0.1 scaling-factor)))
     (make-translate-markup
      (cons x y)
      (make-combine-markup
       (make-draw-circle-markup r th #f)
       (make-override-markup `(thickness . ,scaling-factor)
         (make-combine-markup
          (make-draw-line-markup (cons (- x) (- y)))
          (make-draw-line-markup (cons x y))))))))

% Noticeably thinner than "+" from font -- change?
#(define (make-augmented-markup font-size)
   "Create cross markup for augmented quality."
   (let* ((scaling-factor (magstep font-size))
          (x (* 0.56 scaling-factor))
          (y (* 0.56 scaling-factor)))
     (make-override-markup `(thickness . ,scaling-factor)
       (make-translate-markup (cons x y)
         (make-combine-markup
          (make-combine-markup
           (make-draw-line-markup (cons (- x) 0))
           (make-draw-line-markup (cons 0 (- y))))
          (make-combine-markup
           (make-draw-line-markup (cons x 0))
           (make-draw-line-markup (cons 0 y))))))))

%% TODO: more "science" in the vertical position of quality markers.
#(define (make-quality-markup quality font-size offset)
   (cond
    ;; The quantity 'offset' by itself will cause symbol to rest on the midline.  We
    ;; enlarge offset so that the symbol will be more centered alongside a possible
    ;; figure.  (Topmost figure rests on midline.)
    ((string= quality "o") (make-raise-markup (* offset 1.25) (make-diminished-markup font-size)))
    ((string= quality "h") (make-raise-markup (* offset 1.25) (make-half-diminished-markup font-size)))
    ((string= quality "+") (make-raise-markup (* offset 1.25) (make-augmented-markup font-size)))
    (else (make-raise-markup offset (make-fontsize-markup font-size quality)))))

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% FIGURES %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

#(define (make-figure-markup font-size)
   `(("f" . ,(make-general-align-markup Y DOWN
               (make-fontsize-markup font-size (make-flat-markup))))
     ("ff" . ,(make-general-align-markup Y DOWN
               (make-fontsize-markup font-size (make-doubleflat-markup))))
     ("flat" . ,(make-general-align-markup Y DOWN
                  (make-fontsize-markup font-size (make-flat-markup))))
     ("flatflat" . ,(make-general-align-markup Y DOWN
               (make-fontsize-markup font-size (make-doubleflat-markup))))
     ("s" . ,(make-general-align-markup Y -0.6
               (make-fontsize-markup font-size (make-sharp-markup))))
     ("x" . ,(make-general-align-markup Y -1.9
               (make-fontsize-markup font-size (make-doublesharp-markup))))
     ("ss" . ,(make-general-align-markup Y -1.9
               (make-fontsize-markup font-size (make-doublesharp-markup))))
     ("sharp" . ,(make-general-align-markup Y -0.6
                   (make-fontsize-markup font-size (make-sharp-markup))))
     ("sharpsharp" . ,(make-general-align-markup Y -1.9
               (make-fontsize-markup font-size (make-doublesharp-markup))))
     ("+" . ,(make-general-align-markup Y -1.5 (make-augmented-markup (+ font-size 2))))
     ("n" . ,(make-general-align-markup Y -0.6
               (make-fontsize-markup font-size (make-natural-markup))))
     ("natural" . ,(make-general-align-markup Y -0.6
                     (make-fontsize-markup font-size (make-natural-markup))))
     ))

#(use-modules (ice-9 regex))

#(define (hyphen-to-en-dash str)
   (string-regexp-substitute "-" "â" str))

%% Regular expression for splitting figure strings into words, digits, and connector characters.
#(define figure-regexp (make-regexp "[[:alpha:]]+|[[:digit:]]+|[^[:alnum:]]+"))

#(define (format-figures figures font-size)
   (let ((scaling-factor (magstep font-size)))
     (map (lambda (fig)
            (let* ((parsed-fig (map match:substring (list-matches figure-regexp fig)))
                   ;; Conversion causes character encoding problem with Frescobaldi
                   ;; if done before applying regexp
                   (parsed-fig (map hyphen-to-en-dash parsed-fig)))
              (reduce
               (lambda (elem prev) (make-concat-markup (list prev elem)))
               empty-markup
               (map (lambda (f)
                      (let ((alteration
                             (assoc-ref (make-figure-markup (- font-size 2)) f)))
                        (make-concat-markup
                         (list
                          (if alteration alteration (make-fontsize-markup font-size f))
                          ;; TODO: don't add space at the end
                          (make-hspace-markup (* 0.2 scaling-factor))))))
                 parsed-fig))))
       figures)))

#(define (make-figures-markup figures font-size offset)
   ;; Without offset the column of figures would be positioned such that the
   ;; topmost figure rests on the baseline. Adding offset causes the upper figure
   ;; to rest on the midline of base.
   (let ((formatted-figures (format-figures figures -3)))
     (make-override-markup `(baseline-skip . ,(* 1.4 (magstep font-size)))
       (make-raise-markup offset
         (make-right-column-markup formatted-figures)))))

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% SECONDARY RN %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

#(define (make-secondary-markup second-part scaling-factor)
   (make-concat-markup
    (list
     (car second-part)
     (if (string-null? (cadr second-part))
         empty-markup
         (make-concat-markup
          (list
           (make-hspace-markup (* 0.2 scaling-factor))
           (if (car (parse-string-with-accidental (cadr second-part)))
               (make-hspace-markup (* 0.2 scaling-factor))
               empty-markup)
           (make-base-markup (cadr second-part) scaling-factor)))))))

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% SYNTHESIS %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

#(define-markup-command (rN layout props symbols) (markup-list?)
   #:properties ((font-size 1))
   "Create a symbol for Roman numeral analysis from a @var{symbols}, a list
of strings."
   (let* ((parsed-input (parse-input symbols))
          (first-part (car parsed-input))
          (second-part (cadr parsed-input)) ; slash and what follows
          (base (car first-part))
          (quality (cadr first-part))
          (figures (caddr first-part))
          ;; A multiplier for scaling quantities measured in staff-spaces to
          ;; reflect font-size delta.  Spacing between elements is currently
          ;; controlled by the magstep of the rN font-size.
          (scaling-factor (magstep font-size))
          (base-markup
           (if (or (null? base) (string-null? (car base))) ; "" used as spacer
               #f
               (make-base-markup (car base) scaling-factor)))
          ;; The height of figures and quality determined by midline of base.  If
          ;; there is no base, use forward slash as a representative character.
          (dy (* 0.5
                (interval-length
                 (ly:stencil-extent
                  (interpret-markup
                   layout props (if (markup? base-markup)
                                    base-markup "/"))
                  Y))))
          (quality-markup
           (if (null? quality)
               #f
               (make-concat-markup
                (list
                 (make-hspace-markup (* 0.1 scaling-factor))
                 (make-quality-markup (car quality) -3 dy)))))
          (figures-markup
           (if (null? figures)
               #f
               (make-concat-markup
                (list (make-hspace-markup (* 0.1 scaling-factor))
                  (make-figures-markup figures font-size dy)))))
          (secondary-markup
           (if (null? second-part)
               #f
               (make-concat-markup
                (list
                 (if (= (length figures) 1)
                     ;; allows slash to tuck under if single figure
                     (make-hspace-markup (* -0.2 scaling-factor))
                     ;; slightly more space given to slash
                     (make-hspace-markup (* 0.2 scaling-factor)))
                 (make-secondary-markup second-part scaling-factor)))))
          (visible-markups
           (filter markup?
                   (list base-markup quality-markup figures-markup secondary-markup))))
     (interpret-markup layout props
       (make-concat-markup visible-markups))))

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% KEY INDICATIONS %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

#(define-markup-command (keyIndication layout props arg) (markup?)
   #:properties ((font-size 1))
   "Create a key indicator consisting of a English note name followed by a
colon.  Whitespace after the note name will be included in the returned markup."
   (let* ((scaling-factor (magstep font-size))
          (divide-at-spaces (string-match "([^[:space:]]+)([[:space:]]+)$" arg))
          (base (if divide-at-spaces
                    (match:substring divide-at-spaces 1)
                    arg))
          (trailing-spaces (if divide-at-spaces
                               (match:substring divide-at-spaces 2)
                               empty-markup)))
     (interpret-markup layout props
       (make-concat-markup
        (list
         (make-base-markup base scaling-factor)
         (make-hspace-markup (* 0.2 scaling-factor))
         ":"
         trailing-spaces)))))

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% SCALE DEGREES %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

#(define (parse-scale-degree str alteration-list)
   "Given @var{str}, return a list in this format: (name-of-alteration-or-#f degree)."
   (if (not (string-null? str))
       (let* ((alteration
               (find (lambda (s) (string-prefix? s str)) alteration-list))
              (rest (if alteration
                        (string-drop str (string-length alteration))
                        str)))
         (list alteration rest))))

#(define (hat font-size)
   "Draw a caret for use with scale degrees."
   (let* ((scaling-factor (magstep font-size))
          (x (* 0.25 scaling-factor))
          (y x)
          (th scaling-factor))
     (make-override-markup `(thickness . ,th)
       (make-combine-markup
        (make-draw-line-markup (cons x y))
        (make-translate-markup (cons x y)
          (make-draw-line-markup (cons x (- y))))))))

#(define-markup-command (scaleDegree layout props degree) (markup?)
   #:properties ((font-size 1))
   "Return a digit topped by a caret to represent a scale degree.  Alterations may
be added by prefacing @var{degree} with an English alteration."
   (let* ((scale-factor (magstep font-size))
          (caret (hat font-size))
          (degree-list (parse-scale-degree degree english-alterations))
          (alteration (car degree-list))
          (number (cadr degree-list))
          (alteration-markup (assoc-ref make-accidental-markup alteration))
          (alteration-markup
           (if alteration-markup
               (make-fontsize-markup -3 alteration-markup)
               alteration-markup))
          (number-and-caret
           (make-general-align-markup Y DOWN
             (make-override-markup `(baseline-skip . ,(* 1.7 scale-factor))
               (make-center-column-markup
                (list
                 caret
                 number))))))
     (interpret-markup layout props
       (if alteration-markup
           (make-concat-markup (list
                                alteration-markup
                                number-and-caret))
           number-and-caret))))
"""

# Convenience function to reuse the defined env
def pwrap(args, shell=False):
    p = subprocess.Popen(args, shell=shell, stdout=subprocess.PIPE,
                         stdin=subprocess.PIPE, stderr=subprocess.PIPE,
                         universal_newlines=True)
    return p

# Print output
# http://stackoverflow.com/questions/4417546/constantly-print-subprocess-output-while-process-is-running
def execute(cmd, shell=False):
    popen = pwrap(cmd, shell=shell)
    for stdout_line in iter(popen.stdout.readline, ""):
        yield stdout_line

    popen.stdout.close()
    return_code = popen.wait()
    if return_code:
        raise subprocess.CalledProcessError(return_code, cmd)


def pe(cmd, shell=True):
    """
    Print and execute command on system
    """
    ret = []
    for line in execute(cmd, shell=shell):
        ret.append(line)
        print(line, end="")
    return ret


def music21_extract(p):
    """
    Taken from pthbldr

    Takes in a Music21 score, and outputs dict
    """
    parts = []
    parts_times = []
    parts_delta_times = []
    parts_extras = []
    parts_time_signatures = []
    parts_key_signatures = []
    c = p.chordify()
    ks = p.parts[0].stream().flat.keySignature
    parts_roman_chords = []
    parts_chords = []
    for this_chord in c.recurse().getElementsByClass('Chord'):
        parts_chords.append(this_chord.fullName)
        #print(this_chord.measureNumber, this_chord.beatStr, this_chord)
        rn = roman.romanNumeralFromChord(this_chord, ks.asKey())
        parts_roman_chords.append(rn.figure)

    for i, pi in enumerate(p.parts):
        part = []
        part_time = []
        part_delta_time = []
        part_extras = []
        total_time = 0
        ts = pi.stream().flat.timeSignature
        ks = pi.stream().flat.keySignature
        if len(ks.alteredPitches) == 0:
            parts_key_signatures.append([0])
        else:
            parts_key_signatures.append([ks.sharps])
        parts_time_signatures.append((ts.numerator, ts.denominator))
        for n in pi.stream().flat.notesAndRests:
            if n.isRest:
                part.append(0)
            else:
                try:
                    part.append(n.midi)
                except AttributeError:
                    continue
            if n.tie is not None:
                if n.tie.type == "start":
                    part_extras.append(1)
                elif n.tie.type == "continue":
                    part_extras.append(2)
                elif n.tie.type == "stop":
                    part_extras.append(3)
                else:
                   print("another type of tie?")
                   from IPython import embed; embed(); raise ValueError()
            elif len(n.expressions) > 0:
                print("trill or fermata?")
                from IPython import embed; embed(); raise ValueError()
            else:
                part_extras.append(0)

            part_time.append(total_time + n.duration.quarterLength)
            total_time = part_time[-1]
            part_delta_time.append(n.duration.quarterLength)
        parts.append(part)
        parts_times.append(part_time)
        parts_delta_times.append(part_delta_time)
        parts_extras.append(part_extras)
    return {"parts": parts,
            "parts_times": parts_times,
            "parts_delta_times": parts_delta_times,
            "parts_extras": parts_extras,
            "parts_time_signatures": parts_time_signatures,
            "parts_key_signatures": parts_key_signatures,
            "parts_chords": parts_chords,
            "parts_roman_chords": parts_roman_chords}


def pitch_and_duration_to_piano_roll(list_of_pitch_voices, list_of_duration_voices, min_dur):
    def expand(pitch, dur, min_dur):
        assert len(pitch) == len(dur)
        expanded = [int(d // min_dur) for d in dur]
        check = [d / min_dur for d in dur]
        assert all([e == c for e, c in zip(expanded, check)])
        stretch = [[p] * e for p, e in zip(pitch, expanded)]
        # flatten out to 1 voice
        return [pi for p in stretch for pi in p]

    res = []
    for lpv, ldv in zip(list_of_pitch_voices, list_of_duration_voices):
        qi = expand(lpv, ldv, min_dur)
        res.append(qi)

    min_len = min([len(ri) for ri in res])
    res = [ri[:min_len] for ri in res]
    piano_roll = np.array(res).transpose()
    return piano_roll


def pitches_and_durations_to_pretty_midi(pitches, durations,
                                         save_dir="samples",
                                         name_tag="sample_{}.mid",
                                         add_to_name=0,
                                         lower_pitch_limit=12,
                                         list_of_quarter_length=None,
                                         default_quarter_length=47,
                                         voice_params="woodwinds"):
    # allow list of list of list
    """
    takes in list of list of list, or list of array with axis 0 time, axis 1 voice_number (S,A,T,B)
    outer list is over samples, middle list is over voice, inner list is over time
    durations assumed to be scaled to quarter lengths e.g. 1 is 1 quarter note
    2 is a half note, etc
    """
    is_seq_of_seq = False
    try:
        pitches[0][0]
        durations[0][0]
        if not hasattr(pitches, "flatten") and not hasattr(durations, "flatten"):
            is_seq_of_seq = True
    except:
        raise ValueError("pitches and durations must be a list of array, or list of list of list (time, voice, pitch/duration)")

    if is_seq_of_seq:
        if hasattr(pitches[0], "flatten"):
            # it's a list of array, convert to list of list of list
            pitches = [[[pitches[i][j, k] for j in range(pitches[i].shape[0])] for k in range(pitches[i].shape[1])] for i in range(len(pitches))]
            durations = [[[durations[i][j, k] for j in range(durations[i].shape[0])] for k in range(durations[i].shape[1])] for i in range(len(durations))]


    import pretty_midi
    # BTAS mapping
    def weird():
        voice_mappings = ["Sitar", "Orchestral Harp", "Acoustic Guitar (nylon)",
                          "Pan Flute"]
        voice_velocity = [20, 80, 80, 40]
        voice_offset = [0, 0, 0, 0]
        voice_decay = [1., 1., 1., .95]
        return voice_mappings, voice_velocity, voice_offset, voice_decay

    if voice_params == "weird":
        voice_mappings, voice_velocity, voice_offset, voice_decay = weird()
    elif voice_params == "weird_r":
        voice_mappings, voice_velocity, voice_offset, voice_decay = weird()
        voice_mappings = voice_mappings[::-1]
        voice_velocity = voice_velocity[::-1]
        voice_offset = voice_offset[::-1]
    elif voice_params == "nylon":
        voice_mappings = ["Acoustic Guitar (nylon)"] * 4
        voice_velocity = [20, 16, 25, 10]
        voice_offset = [0, 0, 0, -12]
        voice_decay = [1., 1., 1., 1.]
        voice_decay = voice_decay[::-1]
    elif voice_params == "legend":
        # LoZ
        voice_mappings = ["Acoustic Guitar (nylon)"] * 3 + ["Pan Flute"]
        voice_velocity = [20, 16, 25, 5]
        voice_offset = [0, 0, 0, -12]
        voice_decay = [1., 1., 1., .95]
    elif voice_params == "organ":
        voice_mappings = ["Church Organ"] * 4
        voice_velocity = [40, 30, 30, 60]
        voice_offset = [0, 0, 0, 0]
        voice_decay = [.98, .98, .98, .98]
    elif voice_params == "piano":
        voice_mappings = ["Acoustic Grand Piano"] * 4
        voice_velocity = [40, 30, 30, 60]
        voice_offset = [0, 0, 0, 0]
        voice_decay = [1., 1., 1., 1.]
    elif voice_params == "electric_piano":
        voice_mappings = ["Electric Piano 1"] * 4
        voice_velocity = [40, 30, 30, 60]
        voice_offset = [0, 0, 0, 0]
        voice_decay = [1., 1., 1., 1.]
    elif voice_params == "harpsichord":
        voice_mappings = ["Harpsichord"] * 4
        voice_velocity = [40, 30, 30, 60]
        voice_offset = [0, 0, 0, 0]
        voice_decay = [1., 1., 1., 1.]
    elif voice_params == "woodwinds":
        voice_mappings = ["Bassoon", "Clarinet", "English Horn", "Oboe"]
        voice_velocity = [50, 30, 30, 40]
        voice_offset = [0, 0, 0, 0]
        voice_decay = [1., 1., 1., 1.]
    else:
        # eventually add and define dictionary support here
        raise ValueError("Unknown voice mapping specified")

    # normalize
    mm = float(max(voice_velocity))
    mi = float(min(voice_velocity))
    dynamic_range = min(80, (mm - mi))
    # keep same scale just make it louder?
    voice_velocity = [int((80 - dynamic_range) + int(v - mi)) for v in voice_velocity]

    if not is_seq_of_seq:
        order = durations.shape[-1]
    else:
        try:
            # TODO: reorganize so list of array and list of list of list work
            order = durations[0].shape[-1]
        except:
            order = len(durations[0])
    voice_mappings = voice_mappings[-order:]
    voice_velocity = voice_velocity[-order:]
    voice_offset = voice_offset[-order:]
    voice_decay = voice_decay[-order:]
    if not is_seq_of_seq:
        pitches = [pitches[:, i, :] for i in range(pitches.shape[1])]
        durations = [durations[:, i, :] for i in range(durations.shape[1])]

    n_samples = len(durations)
    for ss in range(n_samples):
        durations_ss = durations[ss]
        pitches_ss = pitches[ss]
        # same number of voices
        assert len(durations_ss) == len(pitches_ss)
        # time length match
        assert all([len(durations_ss[i]) == len(pitches_ss[i]) for i in range(len(pitches_ss))])
        pm_obj = pretty_midi.PrettyMIDI()
        # Create an Instrument instance for a cello instrument
        def mkpm(name):
            return pretty_midi.instrument_name_to_program(name)

        def mki(p):
            return pretty_midi.Instrument(program=p)

        pm_programs = [mkpm(n) for n in voice_mappings]
        pm_instruments = [mki(p) for p in pm_programs]

        if list_of_quarter_length is None:
            # qpm to s per quarter = 60 s per min / quarters per min
            time_scale = 60. / default_quarter_length
        else:
            time_scale = 60. / list_of_quarter_length[ss]

        time_offset = np.zeros((order,))

        # swap so that SATB order becomes BTAS for voice matching
        pitches_ss = pitches_ss[::-1]
        durations_ss = durations_ss[::-1]

        # time
        for ii in range(len(durations_ss[0])):
            # voice
            for jj in range(order):
                try:
                    pitches_isj = pitches_ss[jj][ii]
                    durations_isj = durations_ss[jj][ii]
                except IndexError:
                    # voices may stop short
                    continue
                p = int(pitches_isj)
                d = durations_isj
                if d < 0:
                    continue
                if p < 0:
                    continue
                # hack out the whole last octave?
                s = time_scale * time_offset[jj]
                e = time_scale * (time_offset[jj] + voice_decay[jj] * d)
                time_offset[jj] += d
                if p < lower_pitch_limit:
                    continue
                note = pretty_midi.Note(velocity=voice_velocity[jj],
                                        pitch=p + voice_offset[jj],
                                        start=s, end=e)
                # Add it to our instrument
                pm_instruments[jj].notes.append(note)
        # Add the instrument to the PrettyMIDI object
        for pm_instrument in pm_instruments:
            pm_obj.instruments.append(pm_instrument)
        # Write out the MIDI data

        sv = save_dir + os.sep + name_tag.format(ss + add_to_name)
        try:
            pm_obj.write(sv)
        except ValueError:
            print("Unable to write file {} due to mido error".format(sv))


def quantized_to_pretty_midi(quantized,
                             quantized_bin_size,
                             save_dir="samples",
                             name_tag="sample_{}.mid",
                             add_to_name=0,
                             lower_pitch_limit=12,
                             list_of_quarter_length=None,
                             max_hold_bars=1,
                             default_quarter_length=47,
                             voice_params="woodwinds"):
    """
    takes in list of list of list, or list of array with axis 0 time, axis 1 voice_number (S,A,T,B)
    outer list is over samples, middle list is over voice, inner list is over time
    """

    is_seq_of_seq = False
    try:
        quantized[0][0]
        if not hasattr(quantized[0], "flatten"):
            is_seq_of_seq = True
    except:
        try:
            quantized[0].shape
        except AttributeError:
            raise ValueError("quantized must be a sequence of sequence (such as list of array, or list of list) or numpy array")

    # list of list or mb?
    n_samples = len(quantized)
    all_pitches = []
    all_durations = []

    max_hold = int(max_hold_bars / quantized_bin_size)
    if max_hold < max_hold_bars:
        max_hold = max_hold_bars

    for ss in range(n_samples):
        pitches = []
        durations = []
        if is_seq_of_seq:
            voices = len(quantized[ss])
            qq = quantized[ss]
        else:
            voices = quantized[ss].shape[1]
            qq = quantized[ss].T


        for i in range(voices):
            q = qq[i]
            pitch_i = [0]
            dur_i = []
            cur = 0
            count = 0
            for qi in q:
                if qi != cur:# or count > max_hold:
                    pitch_i.append(qi)
                    quarter_count = quantized_bin_size * (count + 1)
                    dur_i.append(quarter_count)
                    cur = qi
                    count = 0
                else:
                    count += 1
            quarter_count = quantized_bin_size * (count + 1)
            dur_i.append(quarter_count)
            pitches.append(pitch_i)
            durations.append(dur_i)
        all_pitches.append(pitches)
        all_durations.append(durations)
    pitches_and_durations_to_pretty_midi(all_pitches, all_durations,
                                         save_dir=save_dir,
                                         name_tag=name_tag,
                                         add_to_name=add_to_name,
                                         lower_pitch_limit=lower_pitch_limit,
                                         list_of_quarter_length=list_of_quarter_length,
                                         default_quarter_length=default_quarter_length,
                                         voice_params=voice_params)


# rough guide https://www.python-course.eu/python_scores.php
def plot_lilypond(upper_voices, lower_voices=None, own_staves=False,
                  key_signatures=None,
                  time_signatures=None,
                  chord_annotations=None,
                  interval_figures=None,
                  use_clefs=None,
                  fpath="tmp.ly",
                  title="Tmp", composer="Tmperstein", tagline="Copyright:?",
                  x_zoom_bounds=(90, 780), y_zoom_bounds=(50, 220)):
    """
    Expects upper_voices and lower_voices to be list of list

    Needs lilypond, and pdf2svg installed (sudo apt-get install pdf2svg)
    """
    if len(upper_voices) > 1:
        if lower_voices == None and own_staves==False:
            raise ValueError("Multiple voices in upper staff with own_staves=False")
    if use_clefs is None:
        use_clefs = ["treble" for i in range(len(pitches))]
    import matplotlib.pyplot as plt
    import matplotlib.image as mpimg
    # need to align them for chord write T_T
    # for now assume 4/4
    pre = '\\version "2.12.3"'
    pre += roman_include
    minus_keys_flats = ["b", "e", "a", "d", "g", "c", "f"]
    minus_keys_names = ["\key f \major", "\key g \minor",  "\key c \minor",
                        "\key f \minor", "\key bes \minor", "\key ees \minor",
                        "\key aes \minor"]
    minus_keys_flats = minus_keys_flats[::-1]
    minus_keys_names = minus_keys_names[::-1]
    plus_keys_sharps = ["f", "c", "g", "d", "a", "e", "b"]
    plus_keys_names = ["\key g \major", "\key d \major",  "\key a \major",
                       "\key e \major", "\key b \major", "\key fis \major",
                       "\key cis \major"]
    trange = len(upper_voices)
    if lower_voices is not None:
        trange += len(lower_voices)
    if key_signatures is None:
        key_signatures = [[0] for i in range(trange)]
    if time_signatures is None:
        time_signatures = [(4, 1) for i in range(trange)]
    assert len(key_signatures) == trange
    assert len(time_signatures) == trange
    chord_str_pre = """\nanalysis = \lyricmode {
    % \set stanza  = #"G:"
  % For bare Roman numerals, \\rN simply outputs the string."""
    chord_str_post = "\n}\n"
    # this is fake test data
    '''
    chords = """
      \markup \\rN { I }
      I
      \markup \\rN { V 6 5 }
      \markup \\rN { vii o 4 3 / IV }
      \markup \\rN { IV 6 }
      \markup \\rN { ii h 4 3 }
      \markup \\rN { Fr +6 }
      \markup \\rN { I 6 4 }
      \markup \\rN { vii o 7 / vi }
      vi
    """
    '''
    # parse chord annotations
    if chord_annotations is None:
        chord_str = chord_str_pre + chord_str_post
    else:
        chords = ""
        lily_chords = map_music21_romans_to_lilypond(chord_annotations)
        chord_template_pre = "\markup \\rN { "
        chord_template_post = " }\n"
        for n, lc in enumerate(lily_chords):
            if len(lc.strip()) == 1:
                chord_template = lc + "\n"
            else:
                chord_template = chord_template_pre + lc + chord_template_post
            chords += chord_template
            # need to double the first element due to rendering issues in lilypond
            if n == 0:
                chords += chord_template
        chord_str = chord_str_pre + chords + chord_str_post
        chord_str += ""

    pre += chord_str

    if own_staves == False:
        raise ValueError("FIX")
        upper_staff = ""
        lower_staff = ""

        for n, uv in enumerate(upper_voices):
            ksi = key_signatures[n][0]
            tsi = time_signatures[n]
            if ksi != 0:
                if ksi < 0:
                    key_name = minus_keys_names[ksi]
                else:
                    assert ksi - 1 >= 0
                    key_name = plus_keys_names[ksi - 1]
                upper_staff += key_name + " "
                upper_staff += "\\time {}/{}".format(tsi[0], tsi[1]) + " "
            for u in uv:
                upper_staff += u + " "

        if lower_voices is not None:
            for n, lv in lower_voices:
                n_offset = n + len(upper_voices)
                ksi = key_signatures[n_offset][0]
                tsi = time_signatures[n_offset]
                if ksi != 0:
                    if ksi < 0:
                        key_name = minus_keys_names[ksi]
                    else:
                        assert ksi - 1 >= 0
                        key_name = plus_keys_names[ksi - 1]
                    lower_staff += key_name + " "
                    lower_staff += "\\time {}/{}".format(tsi[0], tsi[1]) + " "
                for l in lv:
                    lower_staff += l + " "

        staff = "{\n\\new PianoStaff << \n"
        staff += "  \\new Staff {" + upper_staff + "}\n"
        if lower_staff != "":
            staff += "  \\new Staff { \clef bass " + lower_staff + "}\n"
        staff += ">>\n}\n"
        raise ValueError("upper/lower voice not handled yet")
    else:
        if lower_voices is not None:
            raise ValueError("Put all voices into list of list upper_voices!")
        staff = "{\n\\new StaffGroup << \n"
        for n, v in enumerate(upper_voices):
            this_staff = ""
            ksi = key_signatures[n][0]
            tsi = time_signatures[n]
            if ksi != 0:
                if ksi < 0:
                    key_name = minus_keys_names[ksi]
                else:
                    assert ksi - 1 >= 0
                    key_name = plus_keys_names[ksi - 1]
                this_staff += key_name + " "
                this_staff += "\\time {}/{}".format(tsi[0], tsi[1]) + " "
            for vi in v:
                this_staff += vi + " "

            this_voice = "{}".format("voice{}".format(n))
            staff += '  \\new Voice = "{}"'.format(this_voice) + " {" + '\clef "' + use_clefs[n] + '" ' + this_staff + "}\n"
            if interval_figures is not None and len(interval_figures) > n:
                this_intervals = interval_figures[n]
                intervals_str = ""
                for ti in this_intervals:
                    intervals_str += "<" + str(ti) + "> "
                intervals_str = intervals_str.strip()
                staff += "  \\new FiguredBass \\figuremode { " + intervals_str + " }\n"
            # only the bottom staff...
            if n == trange - 1:
                staff += '  \\new Lyrics \\lyricsto "{}"'.format(this_voice) + " { \\analysis }\n"
        staff += ">>\n}\n"
    title = """\header {{
title = "{}"
composer = "{}"
tagline = "{}"
}}""".format(title, composer, tagline)

    final_ly = pre + staff + title
    with open(fpath, "w") as f:
        f.write(final_ly)

    # also make the pdf?
    # pe("lilypond {}".format(fpath))
    pe("lilypond -fpng {}".format(fpath))
    if len(fpath.split(os.sep)) == 1:
        flist = os.listdir(os.getcwd())
    else:
        flist = os.listdir(str(os.sep).join(fpath.split(os.sep)[:-1]))
    valid_files_name = ".".join(fpath.split(os.sep)[-1].split(".")[:-1])
    flist = [fl for fl in flist if valid_files_name in fl]
    # hardcode to only show 1 page for now...
    flist = [fl for fl in flist if "page1" in fl or "page" not in fl]
    latest_file = max(flist, key=os.path.getctime)
    img = mpimg.imread(latest_file)
    f = plt.figure()
    ax = plt.gca()
    if None in x_zoom_bounds:
        if x_zoom_bounds[-1] is not None:
            raise ValueError("None for x_zoom_bounds only supported on last entry")
        x_zoom_bounds = (x_zoom_bounds[0], img.shape[1])

    if None in y_zoom_bounds:
        if y_zoom_bounds[-1] is not None:
            raise ValueError("None for y_zoom_bounds only supported on last entry")
        y_zoom_bounds = (y_zoom_bounds[0], img.shape[0])
    ax.set_xlim(x_zoom_bounds[0], x_zoom_bounds[1])
    ax.set_ylim(y_zoom_bounds[1], y_zoom_bounds[0])
    ax.imshow(img)
    plt.show()


def map_midi_pitches_to_lilypond(pitches, key_signatures=None):
    # takes in list of list
    # 0 = rest
    # 12 = C0
    # 24 = C1
    # 36 = C2
    # 48 = C3
    # 60 = C4
    # 72 = C5
    # 84 = C6

    # accidentals are key dependent! oy vey
    sharp_notes = ["c", "cis", "d", "dis", "e", "f", "fis", "g", "gis", "a", "ais", "b"]
    flat_notes =  ["c", "des", "d", "ees", "e", "f", "ges", "g", "aes", "a", "bes", "ces"]
    octave_map = [",,,", ",,", ",", "", "'", "''", "'''"]
    minus_keys_flats = ["b", "e", "a", "d", "g", "c", "f"]
    minus_keys_flats = minus_keys_flats[::-1]
    plus_keys_sharps = ["f", "c", "g", "d", "a", "e", "b"]
    rest = "r"
    lily_str_lists = []
    if key_signatures is None:
        key_signatures = [[0] for i in range(len(pitches))]
    use_voice_notes = [sharp_notes if key_signatures[i][0] >= 0 else flat_notes
                       for i in range(len(pitches))]
    assert len(key_signatures) == len(pitches)
    for n, (ks, pv) in enumerate(zip(key_signatures, pitches)):
        use_notes = use_voice_notes[n]
        note_str = [use_notes[int(pvi % 12)] if pvi != 0 else rest for pvi in pv]
        octave_str = [octave_map[int(pvi // 12)] if pvi != 0 else "" for pvi in pv]
        str_list = [ns + os for ns, os in zip(note_str, octave_str)]
        lily_str_lists.append(str_list)
    return lily_str_lists


def map_music21_romans_to_lilypond(chord_annotations):
    #ordered long to short so first match is "best"
    #major_functions = ["I", "II", "III", "IV", "V", "VI", "VII"]
    major_functions = ["VII", "III", "VI", "IV", "II", "V", "I"]
    minor_functions = [mf.lower() for mf in major_functions]
    lilypond_chords = []
    for ca in chord_annotations:
        fca = None
        ext = None
        pre = ""
        if "#" == ca[0]:
            ca = ca[1:]
            pre += ca[0]

        # need to parse it :|
        # try major first, then minor
        if len(ca) > 1:
            for n in range(1, len(ca)):
               for maf, mif in zip(major_functions, minor_functions):
                   if ca[:n] in maf:
                       fca = "".join(ca[:n])
                       ext = " ".join([cai for cai in ca[n:]])
                       pre += ""
                       break
                   elif ca[:n] in mif:
                       fca = "".join(ca[:n])
                       ext = " ".join([cai for cai in ca[n:]])
                       pre += ""
                       break
        elif len(ca) == 1:
            # len == 1
            fca = ca
            ext = ""
            pre += ""
        else:
            print("empty chord annotation!")
            from IPython import embed; embed(); raise ValueError()

        # still no matches!
        if fca is None:
            print("wrong...")
            from IPython import embed; embed(); raise ValueError()

        if fca in major_functions:
            matches = [major_functions[n] for n, ma in enumerate(major_functions) if fca == ma]
        elif fca in minor_functions:
            matches = [minor_functions[n] for n, mi in enumerate(minor_functions) if fca == mi]
        else:
            print("???")
            from IPython import embed; embed(); raise ValueError()
        lily_chord_function = matches[0] + " " + ext
        lilypond_chords.append(lily_chord_function)
    return lilypond_chords


def map_midi_durations_to_lilypond(durations, extras=None):
    # assumed to be relative lengths from quarter note?
    # do I need to make Fraction objects?
    # default is quarter note
    def ff(f):
        return fractions.Fraction(f)

    duration_map = {ff(8.): "\\breve",
                    ff(6.): "1.",
                    ff(4.): "1",
                    ff(3.): "2.",
                    ff(2.): "2",
                    ff(1.): "4",
                    ff(.5): "8",
                    ff(.25): "16",
                    ff(.125): "32",
                    ff(.0625): "64"}

    if extras is None:
        extras = []
        for du in durations:
            e = []
            for diu in du:
                e.append(0)
            extras.append(e)

    lily_str_lists = []
    assert len(durations) == len(extras)
    for dv, ev in zip(durations, extras):
        str_list = []
        assert len(dv) == len(ev)
        for dvi, evi in zip(dv, ev):
            try:
                frac_dvi = duration_map[ff(dvi)]
                if evi != 0:
                   if evi == 1 or evi == 2:
                       frac_dvi += "~"
                str_list.append(frac_dvi)
            except KeyError:
                raise KeyError("No known mapping for duration {}".format(dvi))
        lily_str_lists.append(str_list)
    return lily_str_lists


def pitches_and_durations_to_lilypond_notation(pitches, durations, extras=None,
                                               key_signatures=None):
    lilypitches = map_midi_pitches_to_lilypond(pitches, key_signatures=key_signatures)
    lilydurs = map_midi_durations_to_lilypond(durations, extras)
    assert len(lilypitches) == len(lilydurs)
    lilycomb = []
    for lp, ld in zip(lilypitches, lilydurs):
        assert len(lp) == len(ld)
        lc = [lpi + ldi for lpi, ldi in zip(lp, ld)]
        lilycomb.append(lc)
    return lilycomb


def plot_pitches_and_durations(pitches, durations, extras=None,
                               time_signatures=None,
                               key_signatures=None,
                               chord_annotations=None,
                               interval_figures=None,
                               use_clefs=None):
    # map midi pitches to lilypond ones... oy
    voices = pitches_and_durations_to_lilypond_notation(pitches, durations, extras, key_signatures=key_signatures)
    #plot_lilypond([voices[1]])
    #plot_lilypond([voices[0]], [voices[-1]])
    #plot_lilypond([voices[0]], [voices[-1]], own_staves=True)
    # TODO: fix own_staves=False issues with conflicting time/key signatures
    # raise an error
    # down the line, fix accidentals on case by case basis :|
    # add options for chord notations, and intervals for final analysis
    # add grey notes (all possibles) as well to visualize the decoding?
    plot_lilypond(voices, own_staves=True,
                  time_signatures=time_signatures,
                  key_signatures=key_signatures,
                  chord_annotations=chord_annotations,
                  interval_figures=interval_figures,
                  use_clefs=use_clefs)


def notes_to_midi(notes):
    # r is rest
    # takes in list of list
    # # is sharp
    # b is flat
    # letters should be all caps!
    # C4 = C in 4th octave
    # 0 = rest
    # 12 = C0
    # 24 = C1
    # 36 = C2
    # 48 = C3
    # 60 = C4
    # 72 = C5
    # 84 = C6
    base = {"C": 0,
            "D": 2,
            "E": 4,
            "F": 5,
            "G": 7,
            "A": 9,
            "B": 11}
    pitch_list = []
    for nl in notes:
        pitch_line = []
        for nn in nl:
            if "#" in nn:
                base_pitch = base[nn[0]]
                offset = 1
                octave = (int(nn[-1]) + 1) * 12
            elif "b" in nn:
                base_pitch = base[nn[0]]
                offset = -1
                octave = (int(nn[-1]) + 1) * 12
            else:
                base_pitch = base[nn[0]]
                offset = 0
                octave = (int(nn[-1]) + 1) * 12
            r = base_pitch + octave + offset
            pitch_line.append(r)
        pitch_list.append(pitch_line)
    return pitch_list

def intervals_from_midi(parts, full_name=False):
    if len(parts) < 2:
        raise ValueError("Must be at least 2 parts to compare intervals")
    if len(parts) > 2:
        raise ValueError("NYI")

    intervals = []
    this_intervals = []
    proposed = np.array(parts[0]) - np.array(parts[1])
    for p in proposed:
        # strip off name
        if full_name:
            this_intervals.append(intervals_map[p])
        else:
            nm = intervals_map[p]
            if "-" not in nm:
                this_intervals.append(nm[1:])
            else:
                this_intervals.append(nm[2:])
    intervals.append(this_intervals)
    return intervals

def motion_from_midi(parts):
    if len(parts) != 2:
        raise ValueError("NYI")
    # similar, oblique, contrary, direct
    p0 = np.array(parts[0])
    p1 = np.array(parts[1])
    dp0 = p0[1:] - p0[:-1]
    dp1 = p1[1:] - p1[:-1]
    # first motion is always start...
    motions = ["START"]
    for dip0, dip1 in zip(dp0, dp1):
        if dip0 == 0 or dip1 == 0:
            motions.append("OBLIQUE")
        elif dip0 == dip1:
            motions.append("DIRECT")
        elif dip0 > 0 and dip1 < 0:
            motions.append("CONTRARY")
        elif dip0 < 0 and dip1 > 0:
            motions.append("CONTRARY")
        elif dip0 < 0 and dip1 < 0:
            motions.append("SIMILAR")
        elif dip0 > 0 and dip1 > 0:
            motions.append("SIMILAR")
        else:
            raise ValueError("Should never see this case!")
    motions.append("END")
    return [motions]


def rules_from_midi(parts, key_signature):
    full_intervals = intervals_from_midi(parts, True)
    full_motions = motion_from_midi(parts)
    assert len(full_intervals) == len(full_motions)
    all_rulesets = []
    i = 0
    for fi, fm in zip(full_intervals, full_motions):
        fimi = 0
        this_ruleset = []
        while i < len(fi):
            this_interval = fi[i]
            this_motion = fm[i]
            this_notes = tuple([p[i] for p in parts])
            last_interval = None
            last_motion = None
            last_notes = None
            if i > 0:
                last_interval = fi[i - 1]
                last_notes = tuple([p[i - 1] for p in parts])
                last_motion = fm[i - 1]
            this_ruleset.append(make_rule(this_interval, this_motion, this_notes,
                                          key_signature,
                                          last_interval, last_motion, last_notes))
            i += 1
        all_rulesets.append(this_ruleset)
    return all_rulesets

# previous movement, previous interval, previous notes
rule_template = "{}:{}:{},{}->{}:{}:{},{}"
# key, top note, bottom note
reduced_template = "K{},{},{}->{}:{}:{},{}"

# todo, figure out others...
base_pitch_map = {"C": 0,
                  "C#": 1,
                  "D": 2,
                  "Eb": 3,
                  "E": 4,
                  "F": 5,
                  "F#": 6,
                  "G": 7,
                  "G#": 8,
                  "A": 9,
                  "Bb": 10,
                  "B": 11}
base_note_map = {v: k for k, v in base_pitch_map.items()}

key_signature_map = {0: "C"}
key_check = {"C": ["C", "D", "E", "F", "G", "A", "B"]}
intervals_map = {-16: "-M10",
                -15: "-m10",
                -14: "-M9",
                -13: "-m9",
                -12: "-P8",
                -11: "-m2",
                -10: "-M2",
                -9: "-m3",
                -8: "-M3",
                -7: "-P4",
                -6: "-a4",
                -5: "-P5",
                -4: "-m6",
                -3: "-M6",
                -2: "-m7",
                -1: "-M7",
                0: "P1",
                1: "m2",
                2: "M2",
                3: "m3",
                4: "M3",
                5: "P4",
                6: "a4",
                7: "P5",
                8: "m6",
                9: "M6",
                10: "m7",
                11: "M7",
                12: "P8",
                13: "m9",
                14: "M9",
                15: "m10",
                16: "M10",
                17: "P11",
                18: "a11",
                19: "P12",
                20: "m13",
                21: "M13"}

inverse_intervals_map = {v: k for k, v in intervals_map.items()}

perfect_intervals = {"P1": None,
                     "P8": None,
                     "P5": None,
                     "P4": None}
harmonic_intervals = {"P1": None,
                      "P8": None,
                      "P5": None,
                      "P4": None,
                      "m3": None,
                      "M3": None,
                      "m6": None,
                      "M6": None,
                      "m10": None,
                      "M10": None}
hamonic_intervals = {k: v for k, v in inverse_intervals_map.items()
                     if k in harmonic_intervals}

allowed_perfect_motion = {"CONTRARY": None,
                          "OBLIQUE": None}

def midi_to_notes(parts):
    all_parts = []
    for p in parts:
        this_notes = []
        for pi in p:
            octave = pi // 12 - 1
            pos = base_note_map[pi % 12]
            this_notes.append(pos + str(octave))
        all_parts.append(this_notes)
    return all_parts


def make_rule(this_interval, this_motion, this_notes, key_signature,
              last_interval=None, last_motion=None, last_notes=None):
    if last_interval is not None:
        str_last_notes = midi_to_notes([last_notes])[0]
        str_this_notes = midi_to_notes([this_notes])[0]
        nt = rule_template.format(last_motion, last_interval,
                                  str_last_notes[0], str_last_notes[1],
                                  this_motion, this_interval,
                                  str_this_notes[0], str_this_notes[1])
    else:
        key = key_signature_map[key_signature]
        str_notes = midi_to_notes([this_notes])[0]
        nt = reduced_template.format(key, str_notes[0], str_notes[1], this_motion, this_interval, str_notes[0], str_notes[1])
    return nt


def check_species1_rule(rule, key_signature, mode, parts):
    last, this = rule.split("->")
    key = key_signature_map[key_signature]
    if "K" in last:
        tm, ti, tn = this.split(":")
        lk, lns, lnb = last.split(",")
        # get rid of the K in the front
        lk = lk[1:]
        # check that note is in key?
        if ti == "P8" or ti == "P5":
            if lnb[:-1] == mode:
                return ("First bass note {} matches estimated mode {}".format(lnb, mode), True)
            else:
                return ("First bass note {} doesn't match estimated mode {}".format(lnb, mode), False)
        else:
            return ("First interval {} is not in ['P5', 'P8']".format(ti), False)
    else:
        tm, ti, tn = this.split(":")
        tn0, tn1 = tn.split(",")
        lm, li, ln = last.split(":")
        ln0, ln1 = ln.split(",")
        dn0 = np.diff(np.array(notes_to_midi([[tn0, ln0]])[0]))
        dn1 = np.diff(np.array(notes_to_midi([[tn1, ln1]])[0]))
        note_sets = [[ln0, tn0], [ln1, tn1]]
        for n, voice_step in enumerate([dn0, dn1]):
            this_step = intervals_map[-int(voice_step)]
            if this_step in ["a4", "-a4"]:
                return ("Voice {} stepwise movement {}->{}, {} not allowed".format(n, note_sets[n][0], note_sets[n][1], this_step), False)
        if ti in perfect_intervals:
            if tm in allowed_perfect_motion:
                return ("Movement {} into perfect interval {} allowed".format(tm, ti), True)
            else:
                return ("Movement {} into perfect interval {} not allowed".format(tm, ti), False)
        elif ti in harmonic_intervals:
            return ("All movements including {} allowed into interval {}".format(tm, ti), True)
        else:
            raise ValueError("Shouldn't hit this, current rule is {}".format(rule))
    raise ValueError("This function must return before the end! Bug, rule {}".format(rule))


def estimate_mode(parts, rules, key_signature):
    first_note = [p[0] for p in parts]
    final_notes = [p[-2:] for p in parts]
    final_notes = np.array(final_notes)
    first_note = np.array(first_note)
    dfinal_notes = final_notes[-1, -1] - final_notes[-1, 0]
    if dfinal_notes == 1.:
        # final cadence indicates the tonic
        # bass almost always ends on I, i, etc except in half cadence...
        mode = midi_to_notes([[final_notes[-1, -1]]])[0][0][:-1] # strip octave
        return mode
    elif final_notes[-1, -1] == final_notes[0, 0]:
        mode = midi_to_notes([[final_notes[-1, -1]]])[0][0][:-1] # strip octave
        return mode
    elif rules[-1][-1].split("->")[-1].split(":")[1] in ["P8", "P1"]:
        mode = midi_to_notes([[final_notes[-1, -1]]])[0][0][:-1] # strip octave
        return mode
    else:
        print("Unknown mode estimate...")
        from IPython import embed; embed(); raise ValueError()
    raise ValueError("This function must return before the end! Bug, rule {}".format(rule))


def analyze_rulesets(parts, rules, key_signature):
    rules_ok = []
    for rs in rules:
        this_ok = []
        mode = estimate_mode(parts, rules, key_signature)
        for n, rsi in enumerate(rs):
            r = check_species1_rule(rsi, key_signature, mode, parts)
            this_ok.append(r)
        rules_ok.append(this_ok)
    return rules_ok


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Demo of utils")

    parser.add_argument('-p', action="store_true", default=False)
    args = parser.parse_args()
    print_it = args.p
    # fig 5, gradus ad parnassum
    notes = [["A3", "A3", "G3", "A3", "B3", "C4", "C4", "B3", "D4", "C#4", "D4"],
             ["D3", "F3", "E3", "D3", "G3", "F3", "A3", "G3", "F3", "E3", "D3"]]
    clefs = ["treble", "treble"]
    # fig 6, initial (incorrect) notes
    notes = [["D3", "F3", "E3", "D3", "G3", "F3", "A3", "G3", "F3", "E3", "D3"],
             ["G2", "D3", "A2", "F2", "E2", "D2", "F2", "C3", "D3", "C#3", "D3"]]
    clefs = ["treble", "treble_8"]
    # fig 6, correct notes
    notes = [["D3", "F3", "E3", "D3", "G3", "F3", "A3", "G3", "F3", "E3", "D3"],
             ["D2", "D2", "A2", "F2", "E2", "D2", "F2", "C3", "D3", "C#3", "D3"]]
    clefs = ["treble", "treble_8"]
    # fig 11, correct notes
    notes = [["B3", "C4", "F3", "G3", "A3", "C4", "B3", "E4", "D4", "E4"],
             ["E3", "C3", "D3", "C3", "A2", "A3", "G3", "E3", "F3", "E3"]]
    clefs = ["treble", "treble_8"]
    # fig 12, incorrect notes
    notes = [["E3", "C3", "D3", "C3", "A2", "A3", "G3", "E3", "F3", "E3"],
             ["E2", "A2", "D2", "E2", "F2", "F2", "B2", "C3", "D3", "E3"]]
    clefs = ["treble", "treble_8"]

    parts = notes_to_midi(notes)
    if print_it:
        interval_figures = intervals_from_midi(parts)
        durations = [[4.] * len(notes[0]), [4.] * len(notes[1])]
        # can add harmonic nnotations as well to plot
        #chord_annotations = ["i", "I6", "IV", "V6", "I", "IV6", "I64", "V", "I"]
        time_signatures = [(4, 4), (4, 4)]
        pitches_and_durations_to_pretty_midi([parts], [durations],
                                             save_dir="samples",
                                             name_tag="sample_{}.mid",
                                             default_quarter_length=240,
                                             voice_params="piano")
        plot_pitches_and_durations(parts, durations,
                                   interval_figures=interval_figures,
                                   use_clefs=clefs)

    # C - todo FIX THIS! to handle strings "C"
    key_signature = 0
    rules = rules_from_midi(parts, key_signature)
    aok = analyze_rulesets(parts, rules, key_signature)
    from IPython import embed; embed(); raise ValueError()

