
{ pkgs ? import <nixpkgs> {} }:
(pkgs.python27.buildEnv.override {
  extraLibs = builtins.attrValues (import ./_pip_packages.nix {
    inherit (pkgs) fetchurl;
    inherit (pkgs.python27Packages) buildPythonPackage;
 });
}).env

# with import <nixpkgs> {};
# (pkgs.python27.withPackages (ps: [ps.plumbum ps.future ps.numpy ps.pandas ps.ipython readline])).env
