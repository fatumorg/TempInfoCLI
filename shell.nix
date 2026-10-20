{ pkgs ? import <nixpkgs> {} }:

let
  tempinfocli = import ./default.nix { inherit pkgs; };
in
pkgs.mkShell {
  buildInputs = [
    tempinfocli
    (pkgs.python3.withPackages (ps: with ps; [
      rich
      psutil
      setuptools
      pytest
    ]))
  ];

  shellHook = ''
    echo "tempinfocli dev shell ready. Just run: tempinfo"
  '';
}
